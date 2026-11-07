#!/usr/bin/env python3
"""Static checks for V5 Room Information & Search SAM resources."""

from pathlib import Path
import re
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT_DIR / "infrastructure" / "template.yaml"

ROOM_FUNCTIONS = {
    "GetRoomsFunction": {
        "code_uri": "../lambda/get_rooms/",
        "route": "GET /rooms",
    },
    "GetDetailFunction": {
        "code_uri": "../lambda/get_detail/",
        "route": "GET /rooms/{room_number}",
    },
    "GetRoomScheduleFunction": {
        "code_uri": "../lambda/get_room_schedule/",
        "route": "GET /rooms/{room_number}/schedule",
    },
    "SearchAvailableRoomsFunction": {
        "code_uri": "../lambda/search_available_rooms/",
        "route": "GET /rooms/available",
    },
}


class RoomTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def resource_body(self, resource_name):
        match = re.search(
            rf"(?ms)^  {re.escape(resource_name)}:\n(?P<body>.*?)(?=^  [A-Za-z][A-Za-z0-9]*:\n|\Z)",
            self.template,
        )
        self.assertIsNotNone(match, f"Missing {resource_name} in SAM template")
        return match.group("body")

    def test_database_password_is_parameterized(self):
        body = self.resource_body("DBPassword")
        self.assertIn("Type: String", body)
        self.assertIn("NoEcho: true", body)
        self.assertNotIn("Default:", body)

    def test_shared_pymysql_layer_is_declared(self):
        body = self.resource_body("PyMySqlLayer")
        self.assertIn("Type: AWS::Serverless::LayerVersion", body)
        self.assertIn("ContentUri: ../pymysql-layer/", body)
        self.assertIn("- python3.13", body)

    def test_room_functions_have_required_configuration(self):
        for resource_name, config in ROOM_FUNCTIONS.items():
            with self.subTest(resource=resource_name):
                body = self.resource_body(resource_name)
                self.assertIn("Type: AWS::Serverless::Function", body)
                self.assertIn(f"CodeUri: {config['code_uri']}", body)
                self.assertIn("Handler: lambda_function.lambda_handler", body)
                self.assertIn("Runtime: python3.13", body)
                self.assertIn("- !Ref PyMySqlLayer", body)
                self.assertIn("DB_PASSWORD: !Ref DBPassword", body)
                self.assertIn("- AWSLambdaBasicExecutionRole", body)
                self.assertIn(f"ApiRoute: {config['route']}", body)

                source_dir = ROOT_DIR / config["code_uri"].removeprefix("../")
                self.assertTrue(
                    (source_dir / "lambda_function.py").is_file(),
                    f"Expected Lambda source at {source_dir / 'lambda_function.py'}",
                )


if __name__ == "__main__":
    unittest.main()
