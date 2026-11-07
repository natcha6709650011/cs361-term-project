import os
import unittest
import yaml


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(
    PROJECT_ROOT,
    "infrastructure",
    "modules",
    "room-management.yaml"
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


class TestRoomManagementTemplate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as file:
            cls.template = yaml.load(
                file,
                Loader=CloudFormationLoader
            )

        cls.resources = cls.template["Resources"]

    def test_sam_transform_exists(self):
        self.assertEqual(
            self.template["Transform"],
            "AWS::Serverless-2016-10-31"
        )

    def test_all_three_lambdas_exist(self):
        expected = {
            "ManageRoomFunction",
            "RoomConfigurationFunction",
            "RoomImageUploadFunction"
        }

        self.assertTrue(expected.issubset(self.resources.keys()))

    def test_lambda_handlers_and_code_paths(self):
        for name, resource in self.resources.items():
            if resource["Type"] != "AWS::Serverless::Function":
                continue

            properties = resource["Properties"]

            self.assertEqual(
                properties["Handler"],
                "lambda_function.lambda_handler"
            )

            code_path = os.path.normpath(
                os.path.join(
                    os.path.dirname(TEMPLATE_PATH),
                    properties["CodeUri"]
                )
            )

            self.assertTrue(
                os.path.isfile(
                    os.path.join(code_path, "lambda_function.py")
                ),
                f"Missing Lambda code: {name}"
            )

    def test_database_environment_variables(self):
        for name in [
            "ManageRoomFunction",
            "RoomConfigurationFunction"
        ]:
            variables = self.resources[name]["Properties"][
                "Environment"
            ]["Variables"]

            for key in [
                "DB_HOST",
                "DB_NAME",
                "DB_PORT",
                "DB_USER",
                "DB_PASSWORD"
            ]:
                self.assertIn(key, variables)

    def test_image_bucket_environment_variable(self):
        variables = self.resources[
            "RoomImageUploadFunction"
        ]["Properties"]["Environment"]["Variables"]

        self.assertIn("IMAGE_BUCKET", variables)

    def test_s3_permission_is_scoped(self):
        policies = self.resources[
            "RoomImageUploadFunction"
        ]["Properties"]["Policies"]

        statements = policies[0]["Statement"]

        self.assertTrue(
            any(
                "s3:PutObject" in statement["Action"]
                and statement["Effect"] == "Allow"
                for statement in statements
            )
        )

    def test_requirements_files_exist(self):
        for folder in ["manage_room", "room_configuration"]:
            path = os.path.join(
                PROJECT_ROOT,
                "lambda",
                folder,
                "requirements.txt"
            )
            self.assertTrue(os.path.isfile(path))


if __name__ == "__main__":
    unittest.main()