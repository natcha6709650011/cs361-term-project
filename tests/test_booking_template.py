
"""Static checks for V5: Booking & Booking Lifecycle SAM resources.

Run from the repository root:
    python3 tests/test_booking_template.py
"""

from pathlib import Path
import re
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT_DIR / "infrastructure" / "template.yaml"

BOOKING_FUNCTIONS = {
    "BookingFunction": {
        "code_uri": "../lambda/booking/",
        "timeout": 30,
        "memory": 256,
        "routes": [
            "GET /bookings/me",
            "GET /admin/bookings",
            "POST /bookings",
            "PATCH /bookings/{booking_id}",
            "DELETE /bookings/{booking_id}",
            "POST /bookings/{booking_id}/check-in",
            "POST /bookings/{booking_id}/usage/end",
        ],
    },
    "BookingFacilityManagementFunction": {
        "code_uri": "../lambda/booking_facility_management/",
        "timeout": 30,
        "memory": 256,
        "routes": [
            "GET /approvals/pending",
            "POST /approvals/{booking_id}/decision",
            "POST /rooms/{room_id}/availability",
            "PATCH /facility-schedules/{schedule_id}",
            "POST /facility-schedules/{schedule_id}/cancel",
        ],
    },
    "BookingNoShowFunction": {
        "code_uri": "../lambda/booking_no_show/",
        "timeout": 30,
        "memory": 128,
        "routes": [],
    },
}

REQUIRED_DB_ENV = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT"]

SECRET_PATTERNS = [
    r"(?i)password\s*[:=]\s*['\"]?[A-Za-z0-9!@#$%^&*]{6,}",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)aws_secret_access_key",
]


class BookingTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def resource_body(self, resource_name):
        match = re.search(
            rf"(?ms)^  {re.escape(resource_name)}:\n(?P<body>.*?)(?=^  [A-Za-z][A-Za-z0-9]*:\n|^[A-Za-z]|\Z)",
            self.template,
        )
        self.assertIsNotNone(match, f"Missing {resource_name} in SAM template")
        return match.group("body")

    def globals_body(self):
        match = re.search(r"(?ms)^Globals:\n(?P<body>.*?)(?=^[A-Za-z])", self.template)
        self.assertIsNotNone(match, "Missing Globals section")
        return match.group("body")

    def test_booking_functions_have_required_configuration(self):
        for resource_name, config in BOOKING_FUNCTIONS.items():
            with self.subTest(resource=resource_name):
                body = self.resource_body(resource_name)
                self.assertIn("Type: AWS::Serverless::Function", body)
                self.assertIn(f"CodeUri: {config['code_uri']}", body)
                self.assertIn("Handler: lambda_function.lambda_handler", body)
                self.assertIn("Runtime: python3.13", body)
                self.assertIn(f"Timeout: {config['timeout']}", body)
                self.assertIn(f"MemorySize: {config['memory']}", body)
                self.assertIn("- !Ref PyMySqlLayer", body)
                self.assertIn("Owner: booking-lifecycle", body)

    def test_handler_exists_in_source(self):
        for resource_name, config in BOOKING_FUNCTIONS.items():
            with self.subTest(resource=resource_name):
                source = ROOT_DIR / config["code_uri"].removeprefix("../") / "lambda_function.py"
                self.assertTrue(source.is_file(), f"Expected Lambda source at {source}")
                self.assertRegex(
                    source.read_text(encoding="utf-8"),
                    r"(?m)^def lambda_handler\(event, context\):",
                )

    def test_source_only_depends_on_pymysql_layer(self):
        """Third-party imports must be covered by the shared PyMySQL layer."""
        stdlib = {"base64", "json", "os", "re", "datetime", "decimal"}
        for resource_name, config in BOOKING_FUNCTIONS.items():
            with self.subTest(resource=resource_name):
                source = ROOT_DIR / config["code_uri"].removeprefix("../") / "lambda_function.py"
                modules = set(re.findall(r"(?m)^(?:import|from)\s+([A-Za-z_]\w*)", source.read_text(encoding="utf-8")))
                self.assertEqual(modules - stdlib, {"pymysql"})


    def test_database_environment_variables_are_complete(self):
        globals_body = self.globals_body()
        for name in ["DB_HOST", "DB_NAME", "DB_PORT", "DB_USER"]:
            with self.subTest(variable=name):
                self.assertRegex(globals_body, rf"{name}: !Ref \w+")

        for resource_name in BOOKING_FUNCTIONS:
            with self.subTest(resource=resource_name):
                self.assertIn("DB_PASSWORD: !Ref DBPassword", self.resource_body(resource_name))

    def test_template_covers_env_used_by_code(self):
        declared = set(re.findall(r"(?m)^\s+([A-Z][A-Z0-9_]+): !Ref", self.template))
        for resource_name, config in BOOKING_FUNCTIONS.items():
            source = ROOT_DIR / config["code_uri"].removeprefix("../") / "lambda_function.py"
            required = set(re.findall(r'os\.environ\["([A-Z0-9_]+)"\]', source.read_text(encoding="utf-8")))
            with self.subTest(resource=resource_name):
                self.assertTrue(required <= declared, f"Missing env: {sorted(required - declared)}")

    def test_password_is_not_hardcoded(self):
        body = self.resource_body("DBPassword")
        self.assertIn("NoEcho: true", body)
        self.assertNotIn("Default:", body)
        for pattern in SECRET_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.template))


    def test_iam_is_least_privilege(self):
        for resource_name in BOOKING_FUNCTIONS:
            with self.subTest(resource=resource_name):
                body = self.resource_body(resource_name)
                lines = body.splitlines()
                self.assertIn("      Policies:", lines, "Policies must be declared explicitly")
                start = lines.index("      Policies:") + 1
                entries = []
                for line in lines[start:]:
                    if not line.startswith("        "):
                        break
                    entries.append(line.strip())
                self.assertEqual(entries, ["- AWSLambdaBasicExecutionRole"])
                self.assertNotIn('"*"', body)
                self.assertNotIn("AdministratorAccess", body)

    def test_no_show_schedule_configuration(self):
        body = self.resource_body("BookingNoShowFunction")
        self.assertIn("Events:", body)
        self.assertIn("NoShowSchedule:", body)
        self.assertIn("Type: ScheduleV2", body)  
        self.assertIn("ScheduleExpression: rate(1 minute)", body)  
        self.assertIn("State: !Ref NoShowScheduleState", body)
        self.assertIn("Name: !Sub '${AWS::StackName}-booking-no-show'", body)

    def test_schedule_targets_only_no_show_function(self):
        self.assertEqual(len(re.findall(r"Type: ScheduleV2", self.template)), 1)
        for resource_name in ("BookingFunction", "BookingFacilityManagementFunction"):
            with self.subTest(resource=resource_name):
                self.assertNotIn("Events:", self.resource_body(resource_name))

    def test_schedule_state_parameter(self):
        body = self.resource_body("NoShowScheduleState")
        self.assertIn("Type: String", body)
        self.assertIn("- ENABLED", body)
        self.assertIn("- DISABLED", body)
        self.assertIn("Default: DISABLED", body)

    def test_api_routes_match_lambda_code(self):
        for resource_name, config in BOOKING_FUNCTIONS.items():
            body = self.resource_body(resource_name)
            for route in config["routes"]:
                with self.subTest(resource=resource_name, route=route):
                    self.assertIn(f"- {route}", body)
            if config["routes"]:
                self.assertIn("Authorizer: cstu-jwt-authorizer", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
