
import re
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_PATH = (
    PROJECT_ROOT
    / "infrastructure"
    / "modules"
    / "room-management.yaml"
)


class CloudFormationLoader(yaml.SafeLoader):
    pass


def unknown_tag_constructor(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)

    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)

    return loader.construct_mapping(node)


CloudFormationLoader.add_multi_constructor(
    "!", unknown_tag_constructor
)


class SecurityTemplateTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
            cls.template = yaml.load(
                file,
                Loader=CloudFormationLoader
            )

        cls.parameters = cls.template["Parameters"]
        cls.resources = cls.template["Resources"]

    def test_database_password_is_protected(self):
        """DB password must use NoEcho and must not have a default value."""
        password = self.parameters["DBPassword"]

        self.assertEqual(password["Type"], "String")
        self.assertTrue(password.get("NoEcho", False))
        self.assertNotIn("Default", password)

    def test_database_password_is_not_hardcoded(self):
        """Database password must be referenced from a parameter."""
        for function_name in [
            "ManageRoomFunction",
            "RoomConfigurationFunction"
        ]:
            variables = self.resources[function_name][
                "Properties"
            ]["Environment"]["Variables"]

            self.assertEqual(
                variables["DB_PASSWORD"],
                "DBPassword"
            )

    def test_database_lambdas_have_vpc_configuration(self):
        """Database-connected Lambdas must have VPC configuration."""
        for function_name in [
            "ManageRoomFunction",
            "RoomConfigurationFunction"
        ]:
            properties = self.resources[function_name]["Properties"]

            self.assertIn("VpcConfig", properties)

            vpc_config = properties["VpcConfig"]

            self.assertTrue(vpc_config["SecurityGroupIds"])
            self.assertTrue(vpc_config["SubnetIds"])

    def test_database_lambdas_have_vpc_iam_permission(self):
        """Database-connected Lambdas need VPC execution permissions."""
        for function_name in [
            "ManageRoomFunction",
            "RoomConfigurationFunction"
        ]:
            policies = self.resources[function_name][
                "Properties"
            ]["Policies"]

            self.assertIn(
                "AWSLambdaVPCAccessExecutionRole",
                policies
            )

    def test_image_upload_has_scoped_s3_permission(self):
        """Image upload must only write to the configured bucket."""
        properties = self.resources[
            "RoomImageUploadFunction"
        ]["Properties"]

        policies = properties["Policies"]

        s3_statements = []

        for policy in policies:
            if isinstance(policy, dict):
                s3_statements.extend(
                    policy.get("Statement", [])
                )

        put_object_statements = [
            statement
            for statement in s3_statements
            if "s3:PutObject" in statement.get("Action", [])
        ]

        self.assertTrue(
            put_object_statements,
            "Missing s3:PutObject permission"
        )

        for statement in put_object_statements:
            self.assertEqual(statement["Effect"], "Allow")

            resource = statement["Resource"]

            self.assertEqual(
                resource,
                "arn:${AWS::Partition}:s3:::${ImageBucketName}/*"
            )

    def test_image_upload_does_not_have_broad_s3_permission(self):
        """Image upload must not receive unrestricted S3 permissions."""
        policies = self.resources[
            "RoomImageUploadFunction"
        ]["Properties"]["Policies"]

        for policy in policies:
            if not isinstance(policy, dict):
                continue

            for statement in policy.get("Statement", []):
                actions = statement.get("Action", [])

                if isinstance(actions, str):
                    actions = [actions]

                self.assertNotIn("s3:*", actions)

    def test_image_bucket_environment_variable(self):
        """Image upload must reference the configured bucket."""
        variables = self.resources[
            "RoomImageUploadFunction"
        ]["Properties"]["Environment"]["Variables"]

        self.assertEqual(
            variables["IMAGE_BUCKET"],
            "ImageBucketName"
        )

    def test_no_plaintext_credentials_in_template(self):
        """Template must not contain hardcoded AWS access keys."""
        template_text = TEMPLATE_PATH.read_text(
            encoding="utf-8"
        )

        self.assertIsNone(
            re.search(r"AKIA[0-9A-Z]{16}", template_text)
        )

        self.assertIsNone(
            re.search(
                r"aws_secret_access_key\s*[:=]\s*\S+",
                template_text,
                re.IGNORECASE
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
