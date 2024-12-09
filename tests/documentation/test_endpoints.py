import unittest
from pathlib import Path

class TestEndpointDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "ENDPOINTS.md", "r") as f:
            cls.endpoints_content = f.read().lower()

    def test_all_endpoints_documented(self):
        endpoints = [
            "/route",
            "/costs",
            "/costs/settings",
            "/offer",
            "/data/review"
        ]
        for endpoint in endpoints:
            self.assertIn(endpoint, self.endpoints_content)

    def test_http_methods_documented(self):
        methods = [
            "get",
            "post"
        ]
        for method in methods:
            self.assertIn(method, self.endpoints_content)

    def test_request_parameters_documented(self):
        parameters = [
            "request body",
            "query parameters",
            "optional",
            "required"
        ]
        for param in parameters:
            self.assertIn(param, self.endpoints_content)

    def test_response_formats_documented(self):
        formats = [
            "response (200 ok)",
            "error responses",
            "error response format",
            "json"
        ]
        for fmt in formats:
            self.assertIn(fmt, self.endpoints_content)

    def test_error_handling_documented(self):
        error_elements = [
            "400 bad request",
            "404 not found",
            "422 unprocessable entity",
            "500 internal server error"
        ]
        for element in error_elements:
            self.assertIn(element, self.endpoints_content)

    def test_examples_documented(self):
        example_elements = [
            "request body",
            "response (200 ok)",
            "error responses",
            "json"
        ]
        for element in example_elements:
            self.assertIn(element, self.endpoints_content)

    def test_authentication_documented(self):
        auth_elements = [
            "authentication",
            "publicly accessible",
            "poc"
        ]
        for element in auth_elements:
            self.assertIn(element, self.endpoints_content)
