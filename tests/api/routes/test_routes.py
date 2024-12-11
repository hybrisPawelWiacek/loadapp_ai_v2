import json
from datetime import datetime, timedelta
from uuid import uuid4
from pytz import UTC

def test_create_route(client):
    """Test POST /route endpoint for creating a new route."""
    route_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(UTC).isoformat(),
        "delivery_time": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "transport_type": {
            "name": "Standard Truck",
            "capacity": {"max_weight": 24000, "max_volume": 80},
            "restrictions": []
        },
        "cargo": {
            "type": "General",
            "weight": 15000,
            "value": 50000,
            "special_requirements": []
        }
    }

    response = client.post('/route',
                          data=json.dumps(route_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    created_route = json.loads(response.data)
    
    assert "id" in created_route
    assert created_route["origin_address"] == route_data["origin_address"]
    assert created_route["destination_address"] == route_data["destination_address"]
    assert "total_cost" in created_route
    assert "is_feasible" in created_route
    assert "main_route" in created_route
    assert "empty_driving" in created_route

def test_get_route(client, test_route):
    """Test GET /route/{id} endpoint."""
    response = client.get(f'/route/{test_route.id}')
    
    assert response.status_code == 200
    route_data = json.loads(response.data)
    
    assert route_data["id"] == test_route.id
    assert route_data["origin_address"] == test_route.origin_address
    assert route_data["destination_address"] == test_route.destination_address
    assert route_data["total_cost"] == test_route.total_cost
    assert route_data["is_feasible"] == test_route.is_feasible

def test_get_route_not_found(client):
    """Test GET /route/{id} with non-existent ID."""
    response = client.get(f'/route/{uuid4()}')
    assert response.status_code == 404

def test_create_route_invalid_input(client):
    """Test POST /route with invalid input."""
    # Missing required fields
    invalid_data = {
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050
    }
    
    response = client.post('/route',
                          data=json.dumps(invalid_data),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Invalid coordinates
    invalid_data = {
        "origin_latitude": 1000.0,  # Invalid latitude
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(UTC).isoformat(),
        "delivery_time": (datetime.now(UTC) + timedelta(days=1)).isoformat()
    }
    
    response = client.post('/route',
                          data=json.dumps(invalid_data),
                          content_type='application/json')
    assert response.status_code == 400 