import unittest
import re
from pathlib import Path

class TestEntityDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent.parent
        with open(cls.project_root / "docs" / "ENTITIES.md", "r") as f:
            cls.entities_content = f.read().lower()
        with open(cls.project_root / "project_knowledge" / "o1_mix_final_scope11.md", "r") as f:
            cls.scope_content = f.read().lower()
            
        # Extract dataclass definitions from scope
        cls.dataclass_definitions = {}
        for match in re.finditer(r'@dataclass\s*class\s*(\w+):[^@]*', cls.scope_content, re.DOTALL):
            class_name = match.group(1)
            class_content = match.group(0)
            cls.dataclass_definitions[class_name.lower()] = class_content.lower()

    def test_all_entities_documented(self):
        """Test that all entities from scope are documented."""
        required_entities = [
            "timelineevent",
            "user",
            "businessentity",
            "truckdriverpair",
            "transporttype",
            "cargo",
            "emptydriving",
            "mainroute",
            "route",
            "costitem",
            "offer",
            "location",
            "serviceerror"
        ]
        
        for entity in required_entities:
            self.assertIn(entity, self.entities_content, 
                         f"Entity {entity} is missing from ENTITIES.md")

    def test_entity_fields_documented(self):
        """Test that required fields for each entity are documented."""
        key_fields = {
            "route": ["id", "origin", "destination", "pickup_time", "delivery_time", 
                     "empty_driving", "main_route", "timeline"],
            "offer": ["id", "route_id", "total_cost", "margin", "final_price", 
                     "fun_fact", "status", "created_at"],
            "cargo": ["id", "type", "weight", "value", "special_requirements"],
            "timelineevent": ["type", "location", "time", 
                            "duration_minutes", "description"],
            "costitem": ["id", "type", "category", "base_value", "multiplier", 
                        "currency", "is_enabled"],
            "location": ["latitude", "longitude", "address"]
        }
        
        for entity, fields in key_fields.items():
            entity_section = re.search(
                f'### {entity}.*?(?=###|$)', 
                self.entities_content, 
                re.DOTALL | re.IGNORECASE
            )
            
            if not entity_section:
                self.fail(f"No documentation section found for {entity}")
                
            section_content = entity_section.group(0).lower()
            for field in fields:
                self.assertIn(field, section_content, 
                            f"Field {field} not documented for entity {entity}")

    def test_entity_relationships_documented(self):
        """Test that entity relationships are documented."""
        relationship_keywords = [
            "contains",
            "references",
            "referenced by",
            "associated with",
            "part of",
            "used by",
            "uses",
            "manages",
            "integrates",
            "coordinates"
        ]
        
        entity_sections = re.finditer(
            r'### (\w+)\s+\*\*purpose:\*\*.*?(?=###|$)', 
            self.entities_content, 
            re.DOTALL | re.IGNORECASE
        )
        
        for section in entity_sections:
            section_content = section.group(0).lower()
            entity_name = section.group(1)
            
            # Skip service sections as they are documented separately
            if entity_name.lower().endswith('service'):
                continue
                
            has_relationship = any(keyword in section_content 
                                 for keyword in relationship_keywords)
            
            self.assertTrue(
                has_relationship,
                f"No relationship documentation found for entity {entity_name}"
            )

    def test_service_usage_documented(self):
        """Test that service usage is documented for key entities."""
        required_services = [
            "routeplanningservice",
            "costcalculationservice",
            "offerservice"
        ]
        
        for service in required_services:
            service_mentions = len(re.findall(
                service,
                self.entities_content,
                re.IGNORECASE
            ))
            
            self.assertGreaterEqual(
                service_mentions,
                2,  # Service should be mentioned at least twice (definition + usage)
                f"Service {service} not sufficiently documented in ENTITIES.md"
            )
