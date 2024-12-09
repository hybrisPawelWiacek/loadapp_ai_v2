import unittest
from pathlib import Path

class TestDeveloperGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "DEVELOPER_GUIDE.md", "r") as f:
            cls.guide_content = f.read().lower()

    def test_backend_startup_command(self):
        startup_elements = ["python", "app.py", "backend"]
        for element in startup_elements:
            self.assertIn(element, self.guide_content)

    def test_frontend_startup_command(self):
        startup_elements = ["streamlit run", "frontend"]
        for element in startup_elements:
            self.assertIn(element, self.guide_content)

    def test_test_instructions(self):
        test_elements = ["pytest", "unit test", "integration test"]
        for element in test_elements:
            self.assertIn(element, self.guide_content)

    def test_coding_standards(self):
        standards = ["pep 8", "docstrings", "python code"]
        for standard in standards:
            self.assertIn(standard, self.guide_content)

    def test_contribution_guidelines(self):
        guidelines = ["pull request", "code review", "branch"]
        for guideline in guidelines:
            self.assertIn(guideline, self.guide_content)

    def test_project_structure(self):
        components = ["backend", "frontend", "tests", "docs"]
        for component in components:
            self.assertIn(component, self.guide_content)
