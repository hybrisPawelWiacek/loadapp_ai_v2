from typing import Dict, Any
from datetime import datetime, timedelta

def create_test_route_data() -> Dict[str, Any]:
    """Create test route data with valid values."""
    return {
        "origin": {
            "latitude": 52.5200,
            "longitude": 13.4050,
            "address": "Berlin, Germany"
        },
        "destination": {
            "latitude": 48.1351,
            "longitude": 11.5820,
            "address": "Munich, Germany"
        },
        "pickup_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "delivery_time": (datetime.now() + timedelta(days=2)).isoformat()
    }

def create_test_cargo_data() -> Dict[str, Any]:
    """Create test cargo data with valid values."""
    return {
        "type": "General",
        "weight": 1000.0,
        "value": 5000.0,
        "special_requirements": []
    }

def create_test_transport_data() -> Dict[str, Any]:
    """Create test transport data with valid values."""
    return {
        "name": "Standard Truck",
        "capacity": {
            "max_weight": 20000,
            "max_volume": 100
        },
        "restrictions": []
    }

def assert_valid_route_response(response_data: Dict[str, Any]) -> None:
    """Assert that a route response contains all required fields."""
    assert "id" in response_data
    assert "origin" in response_data
    assert "destination" in response_data
    assert "pickup_time" in response_data
    assert "delivery_time" in response_data
    assert "total_duration_hours" in response_data
    assert "is_feasible" in response_data

def assert_valid_offer_response(response_data: Dict[str, Any]) -> None:
    """Assert that an offer response contains all required fields."""
    assert "id" in response_data
    assert "route_id" in response_data
    assert "total_cost" in response_data
    assert "margin" in response_data
    assert "final_price" in response_data
    assert "status" in response_data
    assert "created_at" in response_data 