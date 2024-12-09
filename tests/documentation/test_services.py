import unittest
from pathlib import Path

class TestServiceDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "SERVICES.md", "r") as f:
            cls.services_content = f.read().lower()

    def test_all_services_documented(self):
        services = [
            "routeplanningservice",
            "costcalculationservice",
            "offerservice"
        ]
        for service in services:
            self.assertIn(service, self.services_content)

    def test_service_responsibilities_documented(self):
        responsibilities = [
            "key responsibilities",
            "purpose",
            "methods"
        ]
        for resp in responsibilities:
            self.assertIn(resp, self.services_content)

    def test_key_methods_documented(self):
        methods = [
            "plan_route",
            "calculate_total_cost",
            "generate_offer",
            "validate",
            "save"
        ]
        for method in methods:
            self.assertIn(method, self.services_content)

    def test_infrastructure_integration_documented(self):
        integrations = [
            "database",
            "repository",
            "openai",
            "logging"
        ]
        for integration in integrations:
            self.assertIn(integration, self.services_content)

    def test_logging_strategy_documented(self):
        logging_elements = [
            "log levels",
            "log structure",
            "logging practices",
            "log storage"
        ]
        for element in logging_elements:
            self.assertIn(element, self.services_content)
