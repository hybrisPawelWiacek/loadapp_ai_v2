import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from pytz import UTC

from backend.flask_app import app
from backend.infrastructure.database.repository import Repository
from backend.infrastructure.database.db_setup import SessionLocal, Base, engine

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
        "duration_validation": True,
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

@pytest.fixture
def test_offer(client, test_route):
    """Create a test offer."""
    data = {
        "route_id": test_route.id,
        "margin": 15.0
    }
    response = client.post('/offer',
                          json=data,
                          content_type='application/json')
    return response.get_json() 