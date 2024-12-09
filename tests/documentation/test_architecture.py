import unittest
import re
from pathlib import Path

class TestArchitecturalDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "ARCHITECTURE.md", "r") as f:
            cls.arch_content = f.read().lower()
        with open(cls.project_root / "docs" / "SCOPE.md", "r") as f:
            cls.scope_content = f.read().lower()

    def test_core_features_documented(self):
        features = ["route planning", "cost calculation", "offer generation"]
        for feature in features:
            self.assertIn(feature, self.arch_content)

    def test_core_services_present(self):
        services = ["route service", "cost service", "offer service"]
        for service in services:
            self.assertIn(service, self.arch_content)

    def test_data_flow_documented(self):
        flow_elements = ["input", "process", "output", "data flow"]
        for element in flow_elements:
            self.assertIn(element, self.arch_content)

    def test_infrastructure_components_present(self):
        components = ["database", "api", "frontend", "backend"]
        for component in components:
            self.assertIn(component, self.arch_content)

    def test_required_layers_present(self):
        """Test that all architectural layers are documented."""
        required_layers = [
            "frontend layer",
            "backend layer",
            "domain layer",
            "infrastructure layer"
        ]
        
        for layer in required_layers:
            self.assertIn(layer, self.arch_content, 
                         f"Missing documentation for {layer}")

    def test_core_services_present(self):
        """Test that all core services are documented."""
        core_services = [
            "routeplanningservice",
            "costcalculationservice",
            "offerservice"
        ]
        
        for service in core_services:
            self.assertIn(service, self.arch_content, 
                         f"Missing documentation for {service}")

    def test_infrastructure_components_present(self):
        """Test that all infrastructure components are documented."""
        components = [
            "sqlite",
            "database",
            "openai",
            "api"
        ]
        
        for component in components:
            self.assertIn(component, self.arch_content, 
                         f"Missing documentation for {component}")

    def test_key_concepts_from_scope(self):
        """Test that key concepts from scope document are reflected in architecture."""
        key_concepts = [
            "domain-driven design",
            "layered architecture",
            "http",
            "json",
            "flask",
            "streamlit"
        ]
        
        for concept in key_concepts:
            self.assertIn(concept, self.arch_content, 
                         f"Missing documentation for {concept}")

    def test_core_features_documented(self):
        """Test that core features from scope are documented."""
        core_features = [
            "route",
            "cost",
            "offer",
            "pickup",
            "delivery"
        ]
        
        for feature in core_features:
            self.assertIn(feature, self.arch_content, 
                         f"Missing documentation for {feature}")

    def test_data_flow_documented(self):
        """Test that data flow is properly documented."""
        data_flow_elements = [
            "user input",
            "http request",
            "database",
            "response"
        ]
        
        for element in data_flow_elements:
            self.assertIn(element, self.arch_content, 
                         f"Missing data flow documentation for {element}")

    def test_future_considerations_present(self):
        considerations = ["real-time", "optimization", "performance"]
        for consideration in considerations:
            self.assertIn(consideration, self.arch_content)

    def test_key_concepts_from_scope(self):
        concepts = ["modularity", "maintainability", "domain"]
        for concept in concepts:
            self.assertIn(concept, self.arch_content)

    def test_scope_alignment(self):
        """Test that no major architectural elements from scope are omitted."""
        arch_pattern = r"(?:^|\n)###[^\n]*(?:\n(?!###)[^\n]*)*"
        scope_sections = re.findall(arch_pattern, self.scope_content)
        for section in scope_sections:
            self.assertTrue(any(word in self.arch_content for word in section.split()))

    def test_performance_monitoring_systems_documented(self):
        """Test that both performance monitoring systems are properly documented."""
        monitoring_components = [
            "performancemetrics",
            "metricslogger",
            "real-time",
            "monitoring",
            "metric aggregation",
            "alert",
            "thread-safe"
        ]
        
        for component in monitoring_components:
            self.assertIn(component, self.arch_content, 
                         f"Missing documentation for {component}")

    def test_performance_metrics_features_documented(self):
        """Test that PerformanceMetrics features are documented."""
        features = [
            "measure_api_response_time",
            "measure_service_operation_time",
            "measure_db_query_time",
            "real-time",
            "minimal overhead",
            "thread-safe"
        ]
        
        for feature in features:
            self.assertIn(feature.lower(), self.arch_content, 
                         f"Missing documentation for {feature}")

    def test_metrics_logger_features_documented(self):
        """Test that MetricsLogger features are documented."""
        features = [
            "long-term",
            "storage",
            "buffer",
            "aggregation",
            "alert rule",
            "1min",
            "5min",
            "1hour",
            "1day"
        ]
        
        for feature in features:
            self.assertIn(feature.lower(), self.arch_content, 
                         f"Missing documentation for {feature}")
