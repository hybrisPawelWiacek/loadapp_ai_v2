import unittest
from pathlib import Path


class TestTestingInfrastructureDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "TESTING_INFRASTRUCTURE.md", "r") as f:
            cls.testing_content = f.read().lower()

    def test_file_exists(self):
        """Test that TESTING_INFRASTRUCTURE.md exists in docs/."""
        file_path = self.project_root / "docs" / "TESTING_INFRASTRUCTURE.md"
        self.assertTrue(file_path.exists(), "TESTING_INFRASTRUCTURE.md should exist in docs/")

    def test_test_categories_documented(self):
        """Test that all test categories are documented."""
        categories = [
            "unit tests",
            "integration tests",
            "documentation tests",
            "ui tests"
        ]
        for category in categories:
            self.assertIn(category, self.testing_content,
                         f"Testing documentation should mention {category}")

    def test_test_locations_documented(self):
        """Test that test directory structure is documented."""
        locations = [
            "tests/domain/",
            "tests/integration/",
            "tests/documentation/",
            "test_flask_endpoints",
            "test_streamlit_ui"
        ]
        for location in locations:
            self.assertIn(location, self.testing_content,
                         f"Testing documentation should mention {location}")

    def test_pytest_commands_documented(self):
        """Test that key pytest commands are documented."""
        commands = [
            "python -m pytest",
            "-v",
            "--cov",
            "tests/domain/",
            "tests/integration/",
            "tests/documentation/"
        ]
        for command in commands:
            self.assertIn(command, self.testing_content,
                         f"Testing documentation should include command: {command}")

    def test_environment_variables_documented(self):
        """Test that required environment variables are documented."""
        env_vars = [
            "openai_api_key",
            "flask_env",
            "sqlite_db_path"
        ]
        for var in env_vars:
            self.assertIn(var, self.testing_content,
                         f"Testing documentation should mention environment variable: {var}")

    def test_naming_conventions_documented(self):
        """Test that naming conventions are documented."""
        conventions = [
            "test_*.py",
            "test*",
            "conftest.py"
        ]
        for convention in conventions:
            self.assertIn(convention, self.testing_content,
                         f"Testing documentation should mention naming convention: {convention}")

    def test_test_guidelines_documented(self):
        """Test that guidelines for adding new tests are documented."""
        guidelines = [
            "fixtures",
            "arrange",
            "act",
            "assert",
            "coverage",
            "mock"
        ]
        for guideline in guidelines:
            self.assertIn(guideline, self.testing_content,
                         f"Testing documentation should mention guideline: {guideline}")

    def test_ci_cd_integration_documented(self):
        """Test that CI/CD integration is documented."""
        ci_cd_elements = [
            "ci/cd",
            "pre-commit",
            "pull request",
            "deployment"
        ]
        for element in ci_cd_elements:
            self.assertIn(element, self.testing_content,
                         f"Testing documentation should mention CI/CD element: {element}")

    def test_test_independence_documented(self):
        """Test that test independence and best practices are documented."""
        practices = [
            "independence",
            "fixtures",
            "clean up",
            "mock",
            "maintenance"
        ]
        for practice in practices:
            self.assertIn(practice, self.testing_content,
                         f"Testing documentation should mention best practice: {practice}")

    def test_example_test_structure_documented(self):
        """Test that an example test structure is provided."""
        example_elements = [
            "class test",
            "def test_",
            "fixture",
            "assert"
        ]
        for element in example_elements:
            self.assertIn(element, self.testing_content,
                         f"Testing documentation should include example with: {element}")
