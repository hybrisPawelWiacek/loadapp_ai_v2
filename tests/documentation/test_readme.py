import unittest
from pathlib import Path

class TestReadmeDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "README.md", "r") as f:
            cls.readme_content = f.read().lower()
        with open(cls.project_root / "project_knowledge" / "o1_mix_final_scope11.md", "r") as f:
            cls.scope_content = f.read().lower()

    def test_project_overview(self):
        overview_elements = [
            "transport management system",
            "route planning",
            "cost calculation",
            "offer generation",
            "cargo transportation",
            "domain-driven design"
        ]
        for element in overview_elements:
            self.assertIn(element, self.readme_content)

    def test_key_features(self):
        features = [
            "route planning",
            "empty driving",
            "cost calculation",
            "offer generation",
            "ai",
            "margin",
            "advanced settings"
        ]
        for feature in features:
            self.assertIn(feature, self.readme_content)

    def test_setup_instructions(self):
        setup_elements = [
            "prerequisites",
            "python",
            "pip",
            "git",
            "virtual environment",
            "requirements.txt",
            "environment variables"
        ]
        for element in setup_elements:
            self.assertIn(element, self.readme_content)

    def test_running_instructions(self):
        run_elements = [
            "backend",
            "frontend",
            "flask",
            "streamlit",
            "localhost:5000",
            "localhost:8501"
        ]
        for element in run_elements:
            self.assertIn(element, self.readme_content)

    def test_documentation_links(self):
        """Test that all documentation files are referenced with correct paths."""
        doc_files = [
            "docs/architecture.md",
            "docs/entities.md",
            "docs/services.md",
            "docs/endpoints.md",
            "docs/frontend_guide.md",
            "docs/developer_guide.md"
        ]
        for doc_file in doc_files:
            self.assertIn(doc_file, self.readme_content)

    def test_project_structure(self):
        structure_elements = [
            "backend",
            "frontend",
            "domain",
            "entities",
            "services",
            "infrastructure",
            "tests",
            "docs",
            "requirements.txt"
        ]
        for element in structure_elements:
            self.assertIn(element, self.readme_content)

    def test_technology_stack(self):
        technologies = [
            "streamlit",
            "flask",
            "sqlite",
            "openai",
            "pytest",
            "structlog"
        ]
        for tech in technologies:
            self.assertIn(tech, self.readme_content)
