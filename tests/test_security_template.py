
"""Static tests for V5 Authentication & Security SAM resources.

Run from the repository root:
    py -3 tests/test_security_template.py -v
"""

from pathlib import Path
import re
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT_DIR / "infrastructure" / "template.yaml"

MODULE_FUNCTIONS = {
    "UserAuthFunction": {
        "code_uri": "../lambda/cstu-user-auth/",
        "timeout": 30,
        "memory": 256,
        "owner": "authentication-security",
        "requirements": {
            "pyjwt", "pymysql", "cryptography", "boto3"
        },
    },
    "JwtAuthorizerFunction": {
        "code_uri": "../lambda/cstu-jwt-authorizer/",
        "timeout": 10,
        "memory": 128,
        "owner": "authentication-security",
        "requirements": {
            "pyjwt", "cryptography"
        },
    },
    "CstuRoomPermissionFunction": {
        "code_uri": "../lambda/cstu-room-permission/",
        "timeout": 30,
        "memory": 256,
        "owner": "authentication-security",
        "requirements": {
            "pyjwt", "pymysql", "cryptography"
        },
    },
}

REQUIRED_ENV = {
    "UserAuthFunction": [
        "DB_PASSWORD: !Sub '{{resolve:secretsmanager:${DBPasswordSecretArn}:SecretString:password}}'",
        "TU_API_URL: !Ref TuApiUrl",
        "TU_API_KEY_SECRET_ARN: !Ref TuApiKeySecret",
        "JWT_PRIVATE_KEY_SECRET_ARN: !Ref JwtPrivateKeySecret",
        "FRONTEND_ORIGIN: !Ref FrontendOrigin",
    ],
    "CstuRoomPermissionFunction": [
        "DB_PASSWORD: !Sub '{{resolve:secretsmanager:${DBPasswordSecretArn}:SecretString:password}}'",
    ],
}

REQUIRED_SECRETS = [
    "JwtPrivateKeySecret",
    "TuApiKeySecret",
]

REQUIRED_OUTPUTS = [
    "UserAuthFunctionArn",
    "JwtAuthorizerFunctionArn",
    "CstuRoomPermissionFunctionArn",
    "JwtAuthorizerUri",
    "RoomPermissionAuthorizerUri",
    "JwtPrivateKeySecretArn",
    "TuApiKeySecretArn",
]


class SecurityTemplateTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not TEMPLATE_PATH.is_file():
            raise FileNotFoundError(
                f"SAM template not found: {TEMPLATE_PATH}"
            )

        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def resource_body(self, resource_name):
        pattern = (
            rf"(?ms)^  {re.escape(resource_name)}:\n"
            rf"(?P<body>.*?)"
            rf"(?=^  [A-Za-z][A-Za-z0-9]*:\s*$"
            rf"|^[A-Za-z][A-Za-z0-9]*:\s*$|\Z)"
        )

        match = re.search(pattern, self.template)

        self.assertIsNotNone(
            match,
            f"Missing resource: {resource_name}"
        )

        return match.group("body")

    def section_body(self, section_name):
        pattern = (
            rf"(?ms)^{re.escape(section_name)}:\n"
            rf"(?P<body>.*?)"
            rf"(?=^[A-Za-z][A-Za-z0-9]*:\s*$|\Z)"
        )

        match = re.search(pattern, self.template)

        self.assertIsNotNone(
            match,
            f"Missing section: {section_name}"
        )

        return match.group("body")

    def test_security_lambda_resources_exist(self):
        for name in MODULE_FUNCTIONS:
            with self.subTest(resource=name):
                body = self.resource_body(name)
                self.assertIn(
                    "Type: AWS::Serverless::Function",
                    body
                )

    def test_lambda_configuration(self):
        for name, config in MODULE_FUNCTIONS.items():
            with self.subTest(resource=name):
                body = self.resource_body(name)

                self.assertIn(
                    f"CodeUri: {config['code_uri']}",
                    body
                )
                self.assertIn(
                    "Handler: lambda_function.lambda_handler",
                    body
                )
                self.assertIn("Runtime: python3.13", body)
                self.assertIn(
                    f"Timeout: {config['timeout']}",
                    body
                )
                self.assertIn(
                    f"MemorySize: {config['memory']}",
                    body
                )
                self.assertIn(
                    f"Owner: {config['owner']}",
                    body
                )

    def test_source_handler_exists(self):
        for name, config in MODULE_FUNCTIONS.items():
            with self.subTest(resource=name):
                folder = (
                    config["code_uri"]
                    .removeprefix("../")
                )

                source = (
                    ROOT_DIR / folder / "lambda_function.py"
                )

                self.assertTrue(
                    source.is_file(),
                    f"Missing Lambda source: {source}"
                )

                source_text = source.read_text(
                    encoding="utf-8"
                )

                self.assertRegex(
                    source_text,
                    r"(?m)^def lambda_handler\(event, context\):"
                )

    def test_dependencies_are_complete(self):
        for name, config in MODULE_FUNCTIONS.items():
            with self.subTest(resource=name):
                folder = config["code_uri"].removeprefix("../")
                requirements = (
                    ROOT_DIR / folder / "requirements.txt"
                )

                self.assertTrue(
                    requirements.is_file(),
                    f"Missing requirements.txt: {requirements}"
                )

                packages = set()

                for line in requirements.read_text(
                    encoding="utf-8"
                ).splitlines():

                    # Remove UTF-8 BOM and surrounding whitespace
                    line = line.strip().lstrip("\ufeff")

                    if not line or line.startswith("#"):
                        continue

                    package = re.split(
                        r"[<=>~!]",
                        line,
                        maxsplit=1
                    )[0].lower().replace("-", "_")

                    packages.add(package)

                self.assertTrue(
                    config["requirements"] <= packages,
                    f"Missing dependencies: "
                    f"{config['requirements'] - packages}"
                )

    def test_public_keys_exist(self):
        for folder in [
            "cstu-jwt-authorizer",
            "cstu-room-permission",
        ]:
            with self.subTest(folder=folder):
                public_key = (
                    ROOT_DIR / "lambda" / folder / "public.pem"
                )

                self.assertTrue(
                    public_key.is_file(),
                    f"Missing public.pem in {folder}"
                )

                self.assertGreater(
                    public_key.stat().st_size,
                    0
                )

    def test_public_keys_are_identical(self):
        key_a = (
            ROOT_DIR / "lambda" / "cstu-jwt-authorizer" / "public.pem"
        )
        key_b = (
            ROOT_DIR / "lambda" / "cstu-room-permission" / "public.pem"
        )

        self.assertEqual(
            key_a.read_bytes(),
            key_b.read_bytes(),
            "Public Keys must be identical"
        )

    def test_kid_is_consistent(self):
        expected = {}

        patterns = {
            "UserAuthFunction": r'KID\s*=\s*["\']([^"\']+)["\']',
            "JwtAuthorizerFunction":
                r'EXPECTED_KID\s*=\s*["\']([^"\']+)["\']',
            "CstuRoomPermissionFunction":
                r'EXPECTED_KID\s*=\s*["\']([^"\']+)["\']',
        }

        for name, config in MODULE_FUNCTIONS.items():
            folder = config["code_uri"].removeprefix("../")
            source = (
                ROOT_DIR / folder / "lambda_function.py"
            ).read_text(encoding="utf-8")

            match = re.search(patterns[name], source)

            self.assertIsNotNone(
                match,
                f"Missing KID in {name}"
            )

            expected[name] = match.group(1)

        self.assertEqual(
            len(set(expected.values())),
            1,
            f"KID mismatch: {expected}"
        )

        self.assertRegex(
            expected["UserAuthFunction"],
            r"^[a-f0-9]{16}$"
        )

    def test_secret_resources_exist(self):
        for name in REQUIRED_SECRETS:
            with self.subTest(secret=name):
                body = self.resource_body(name)

                self.assertIn(
                    "Type: AWS::SecretsManager::Secret",
                    body
                )
                self.assertIn("DeletionPolicy: Retain", body)
                self.assertNotRegex(
                    body,
                    r"(?m)^\s*SecretString:"
                )

    def test_auth_environment_variables(self):
        body = self.resource_body("UserAuthFunction")

        for variable in REQUIRED_ENV["UserAuthFunction"]:
            with self.subTest(variable=variable):
                self.assertIn(variable, body)

    def test_mock_login_disabled_by_default_and_dev_only(self):
        parameters = self.section_body("Parameters")
        conditions = self.section_body("Conditions")
        auth_body = self.resource_body("UserAuthFunction")

        self.assertIn("MockLoginEnabled:", parameters)
        self.assertIn("Default: 'false'", parameters)

        self.assertIn("AllowMockLogin: !And", conditions)
        self.assertIn(
            "!Equals [!Ref Environment, dev]",
            conditions
        )
        self.assertIn(
            "!Equals [!Ref MockLoginEnabled, 'true']",
            conditions
        )

        self.assertIn(
            "MOCK_LOGIN_ENABLED: !If [AllowMockLogin, 'true', 'false']",
            auth_body
        )

    def test_mock_login_requires_explicit_environment_flag(self):
        source = (
            ROOT_DIR
            / "lambda"
            / "cstu-user-auth"
            / "lambda_function.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'if os.environ.get("MOCK_LOGIN_ENABLED", "false").lower() == "true":',
            source
        )

    def test_permission_database_environment(self):
        body = self.resource_body("CstuRoomPermissionFunction")

        for variable in REQUIRED_ENV["CstuRoomPermissionFunction"]:
            with self.subTest(variable=variable):
                self.assertIn(variable, body)

        globals_body = self.section_body("Globals")

        for variable in [
            "DB_HOST: !Ref DBHost",
            "DB_NAME: !Ref DBName",
            "DB_PORT: !Ref DBPort",
            "DB_USER: !Ref DBUser",
        ]:
            with self.subTest(variable=variable):
                self.assertIn(variable, globals_body)

    def test_auth_iam_is_least_privilege(self):
        body = self.resource_body("UserAuthFunction")

        self.assertIn(
            "AWSLambdaBasicExecutionRole",
            body
        )
        self.assertIn(
            "secretsmanager:GetSecretValue",
            body
        )
        self.assertIn(
            "- !Ref JwtPrivateKeySecret",
            body
        )
        self.assertIn(
            "- !Ref TuApiKeySecret",
            body
        )

        self.assertNotIn(
            "Resource: '*'",
            body
        )
        self.assertNotIn(
            "Action: '*'",
            body
        )

    def test_other_lambdas_do_not_receive_secret_access(self):
        for name in [
            "JwtAuthorizerFunction",
            "CstuRoomPermissionFunction",
        ]:
            with self.subTest(resource=name):
                body = self.resource_body(name)

                self.assertIn(
                    "AWSLambdaBasicExecutionRole",
                    body
                )
                self.assertNotIn(
                    "secretsmanager:GetSecretValue",
                    body
                )

    def test_private_key_is_not_in_lambda_source(self):
        lambda_dir = ROOT_DIR / "lambda"

        private_keys = list(
            lambda_dir.rglob("private.pem")
        )

        self.assertEqual(
            private_keys,
            [],
            f"Private Key found in Lambda source: {private_keys}"
        )

    
    
   
    def test_database_password_is_not_hardcoded(self):
        parameters = self.section_body("Parameters")
        match = re.search(
            r"(?ms)^  DBPasswordSecretArn:\n(?P<body>.*?)(?=^  [A-Za-z][A-Za-z0-9]*:\s*$|\Z)",
            parameters
        )
        self.assertIsNotNone(match, "Missing DBPasswordSecretArn parameter")
        self.assertIn("Type: String", match.group("body"))
        self.assertNotIn("Default:", match.group("body"))




    def test_outputs_exist(self):
        outputs = self.section_body("Outputs")

        for name in REQUIRED_OUTPUTS:
            with self.subTest(output=name):
                self.assertRegex(
                    outputs,
                    rf"(?m)^  {re.escape(name)}:"
                )

    def test_secret_values_are_not_hardcoded_in_template(self):
        self.assertNotRegex(
            self.template,
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
