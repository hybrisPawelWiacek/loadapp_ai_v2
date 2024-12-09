import unittest
from pathlib import Path

class TestFrontendDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "FRONTEND_GUIDE.md", "r") as f:
            cls.frontend_content = f.read().lower()

    def test_pages_documented(self):
        pages = [
            "home",
            "offer review",
            "cost settings"
        ]
        for page in pages:
            self.assertIn(page, self.frontend_content)

    def test_components_documented(self):
        components = [
            "form",
            "button",
            "input",
            "filter",
            "navigation"
        ]
        for component in components:
            self.assertIn(component, self.frontend_content)

    def test_user_actions_documented(self):
        actions = [
            "submit",
            "calculate",
            "generate",
            "review",
            "save"
        ]
        for action in actions:
            self.assertIn(action, self.frontend_content)

    def test_form_interactions_documented(self):
        interactions = [
            "input validation",
            "error message",
            "invalid input",
            "loading indicator",
            "validation"
        ]
        for interaction in interactions:
            self.assertIn(interaction, self.frontend_content)

    def test_error_handling_documented(self):
        error_elements = [
            "invalid input",
            "network connectivity",
            "backend service errors",
            "error message",
            "missing or invalid data"
        ]
        for element in error_elements:
            self.assertIn(element, self.frontend_content)

    def test_browser_compatibility_documented(self):
        browsers = [
            "chrome",
            "firefox",
            "safari",
            "edge"
        ]
        for browser in browsers:
            self.assertIn(browser, self.frontend_content)

    def test_user_instructions_documented(self):
        instructions = [
            "getting started",
            "launching",
            "guide",
            "tips",
            "support"
        ]
        for instruction in instructions:
            self.assertIn(instruction, self.frontend_content)
