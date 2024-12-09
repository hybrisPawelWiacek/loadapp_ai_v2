import pytest
import json
from datetime import datetime, timedelta
from backend.flask_app import app
from backend.domain.entities import Route, Location, Cargo, TransportType

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_full_workflow(client):
    """Test the complete workflow from route calculation to offer generation."""
    # 1. Calculate route
    route_data = {
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
        "delivery_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "cargo": {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "STANDARD",
            "weight": 1000.0,
            "value": 5000.0,
            "special_requirements": []
        },
        "transport_type": {
            "id": "87654321-4321-8765-4321-876543210987",
            "name": "TRUCK",
            "capacity": {
                "max_weight": 24000.0,
                "max_volume": 80.0,
                "unit": "metric"
            },
            "restrictions": []
        }
    }
    
    response = client.post('/route',
                         json=route_data,
                         content_type='application/json')
    assert response.status_code == 200
    route_result = json.loads(response.data)
    assert 'id' in route_result
    route_id = route_result['id']

    # 2. Calculate costs
    cost_response = client.post(f'/costs/{route_id}',
                              json={"include_empty_driving": True},
                              content_type='application/json')
    assert cost_response.status_code == 200
    cost_result = json.loads(cost_response.data)
    assert 'total_cost' in cost_result
    
    # 3. Generate offer
    offer_data = {
        "route_id": route_id,
        "margin": 15
    }
    offer_response = client.post('/offer',
                               json=offer_data,
                               content_type='application/json')
    assert offer_response.status_code == 201
    offer_result = json.loads(offer_response.data)
    assert 'id' in offer_result
    assert 'total_price' in offer_result
    
    # 4. Review offers
    review_response = client.get('/data/review')
    assert review_response.status_code == 200
    offers = json.loads(review_response.data)
    assert isinstance(offers, list)
    assert len(offers) > 0
    
def test_cost_settings(client):
    """Test cost settings management."""
    # 1. Get current settings
    response = client.get('/costs/settings')
    assert response.status_code == 200
    settings = json.loads(response.data)
    assert isinstance(settings, list)
    
    # 2. Update a setting
    if settings:
        setting = settings[0]
        update_data = {
            "enabled": not setting['enabled'],
            "value": setting['value'] + 10 if isinstance(setting['value'], (int, float)) else setting['value']
        }
        response = client.put(f'/costs/settings/{setting["id"]}',
                            json=update_data,
                            content_type='application/json')
        assert response.status_code == 200
        
        # 3. Verify update
        response = client.get('/costs/settings')
        assert response.status_code == 200
        updated_settings = json.loads(response.data)
        updated_setting = next(s for s in updated_settings if s['id'] == setting['id'])
        assert updated_setting['enabled'] == update_data['enabled']
        if isinstance(setting['value'], (int, float)):
            assert updated_setting['value'] == update_data['value']

def test_error_handling(client):
    """Test error handling for invalid inputs."""
    # Test missing required fields
    response = client.post('/route',
                         json={},
                         content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid route ID
    response = client.post('/costs/invalid-id',
                         json={"include_empty_driving": True},
                         content_type='application/json')
    assert response.status_code == 404
