import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import json
from backend.flask_app import app
from backend.domain.entities import Location, Route, TransportType, Cargo
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.database.db_setup import SessionLocal, Base, engine
from pytz import UTC

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_route(db):
    """Create a test route in the database."""
    repository = Repository(db)
    route_data = {
        "id": str(uuid4()),
        "origin_latitude": 52.5200,
        "origin_longitude": 13.4050,
        "origin_address": "Berlin, Germany",
        "destination_latitude": 48.8566,
        "destination_longitude": 2.3522,
        "destination_address": "Paris, France",
        "pickup_time": datetime.now(UTC),
        "delivery_time": (datetime.now(UTC) + timedelta(days=1)),
        "total_duration_hours": 10.5,
        "is_feasible": True,
        "duration_validation": True,  # Explicitly set as boolean
        "transport_type": {
            "id": str(uuid4()),
            "name": "Standard Truck",
            "capacity": {"max_weight": 24000, "max_volume": 80},
            "restrictions": []
        },
        "cargo": {
            "id": str(uuid4()),
            "type": "General",
            "weight": 15000,
            "value": 50000,
            "special_requirements": []
        },
        "total_cost": 1500.0,
        "currency": "EUR",
        "empty_driving": {
            "distance_km": 200.0,
            "duration_hours": 4.0,
            "base_cost": 100.0
        },
        "main_route": {
            "distance_km": 1050.0,
            "duration_hours": 10.5,
            "country_segments": [
                {
                    "country": "DE",
                    "distance_km": 500.0,
                    "duration_hours": 5.0
                },
                {
                    "country": "FR",
                    "distance_km": 550.0,
                    "duration_hours": 5.5
                }
            ]
        }
    }
    route = repository.create_route(route_data)
    return route

@pytest.fixture
def test_cost_settings(db):
    """Create test cost settings in the database."""
    repository = Repository(db)
    settings_data = [
        {
            "id": str(uuid4()),
            "type": "fuel",
            "category": "variable",
            "base_value": 1.5,
            "multiplier": 1.0,
            "currency": "EUR",
            "is_enabled": True,
            "description": "Fuel cost per kilometer"
        },
        {
            "id": str(uuid4()),
            "type": "driver",
            "category": "fixed",
            "base_value": 200.0,
            "multiplier": 1.0,
            "currency": "EUR",
            "is_enabled": True,
            "description": "Driver daily rate"
        }
    ]
    return repository.save_cost_settings(settings_data)

def test_create_offer(client, test_route):
    """Test /offer endpoint for creating an offer with fun fact."""
    # Prepare test data
    data = {
        "route_id": test_route.id,
        "margin": 15.0
    }

    # Make request to create offer
    response = client.post('/offer',
                          data=json.dumps(data),
                          content_type='application/json')
    
    # Check response
    assert response.status_code == 201
    offer_data = json.loads(response.data)
    
    # Verify offer structure
    assert "id" in offer_data
    assert "route_id" in offer_data
    assert "total_price" in offer_data
    assert "margin" in offer_data
    assert "fun_fact" in offer_data
    assert offer_data["route_id"] == test_route.id
    assert offer_data["margin"] == 15.0
    assert isinstance(offer_data["fun_fact"], str)
    assert len(offer_data["fun_fact"]) > 0

def test_create_offer_invalid_input(client):
    """Test /offer endpoint with invalid input."""
    # Test missing route_id
    response = client.post('/offer',
                          data=json.dumps({"margin": 15.0}),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test missing margin
    response = client.post('/offer',
                          data=json.dumps({"route_id": str(uuid4())}),
                          content_type='application/json')
    assert response.status_code == 400

def test_review_offers(client, test_route):
    """Test /data/review endpoint for reviewing past offers."""
    # First create an offer
    offer_data = {
        "route_id": test_route.id,
        "margin": 15.0
    }
    client.post('/offer',
                data=json.dumps(offer_data),
                content_type='application/json')

    # Get offers review
    response = client.get('/data/review')
    
    # Check response
    assert response.status_code == 200
    review_data = json.loads(response.data)
    
    # Verify review data structure
    assert "offers" in review_data
    assert "total_count" in review_data
    assert isinstance(review_data["offers"], list)
    assert review_data["total_count"] > 0
    
    # Verify offer details
    offer = review_data["offers"][0]
    assert "id" in offer
    assert "route_id" in offer
    assert "total_price" in offer
    assert "margin" in offer
    assert "fun_fact" in offer
    assert offer["route_id"] == test_route.id
    assert offer["margin"] == 15.0
    assert isinstance(offer["fun_fact"], str)

def test_get_cost_settings(client, test_cost_settings):
    """Test GET /costs/settings endpoint."""
    # Make request to get cost settings
    response = client.get('/costs/settings')
    
    # Check response
    assert response.status_code == 200
    settings_data = json.loads(response.data)
    
    # Verify we got a list of settings
    assert isinstance(settings_data, list)
    assert len(settings_data) == len(test_cost_settings)
    
    # Verify each setting has the correct structure and data
    for setting in settings_data:
        assert set(setting.keys()) == {
            'id', 'type', 'category', 'base_value', 'multiplier',
            'currency', 'is_enabled', 'description'
        }
        # Find corresponding test setting
        test_setting = next(
            s for s in test_cost_settings 
            if str(s.id) == setting['id']
        )
        assert setting['type'] == test_setting.type
        assert setting['category'] == test_setting.category
        assert setting['base_value'] == test_setting.base_value
        assert setting['multiplier'] == test_setting.multiplier
        assert setting['currency'] == test_setting.currency
        assert setting['is_enabled'] == test_setting.is_enabled
        assert setting['description'] == test_setting.description

def test_update_cost_settings(client, test_cost_settings):
    """Test POST /costs/settings endpoint."""
    # Prepare update data
    updates = [
        {
            'id': str(test_cost_settings[0].id),
            'base_value': 2.0,
            'is_enabled': False
        },
        {
            'id': str(test_cost_settings[1].id),
            'multiplier': 1.5
        }
    ]
    
    # Make request to update settings
    response = client.post(
        '/costs/settings',
        data=json.dumps(updates),
        content_type='application/json'
    )
    
    # Check response
    assert response.status_code == 200
    updated_settings = json.loads(response.data)
    assert len(updated_settings) == len(updates)
    
    # Verify updates were applied
    for updated, original_update in zip(updated_settings, updates):
        assert str(updated['id']) == original_update['id']
        for key, value in original_update.items():
            if key != 'id':
                assert updated[key] == value
    
    # Verify changes persisted by getting settings again
    response = client.get('/costs/settings')
    assert response.status_code == 200
    settings_data = json.loads(response.data)
    
    # Find and verify updated settings
    for update in updates:
        setting = next(
            s for s in settings_data 
            if s['id'] == update['id']
        )
        for key, value in update.items():
            if key != 'id':
                assert setting[key] == value

def test_update_cost_settings_invalid_input(client, test_cost_settings):
    """Test POST /costs/settings endpoint with invalid input."""
    # Test with non-list input
    response = client.post(
        '/costs/settings',
        data=json.dumps({'not': 'a list'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    
    # Test with missing id
    response = client.post(
        '/costs/settings',
        data=json.dumps([{'base_value': 2.0}]),
        content_type='application/json'
    )
    assert response.status_code == 400
    
    # Test with non-existent id
    response = client.post(
        '/costs/settings',
        data=json.dumps([{
            'id': str(uuid4()),
            'base_value': 2.0
        }]),
        content_type='application/json'
    )
    assert response.status_code == 404
