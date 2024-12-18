import pytest
from datetime import datetime, timedelta
import json
from uuid import uuid4

from backend.flask_app import app
from backend.domain.services import RoutePlanningService, CostCalculationService
from backend.domain.services.offer import OfferService

@pytest.fixture
def client(mock_db, mock_ai_service):
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    
    # Save original services
    original_repo = app.get_repository()
    original_offer_service = app.get_offer_service()
    
    # Replace services with test versions
    app.set_repository(mock_db)
    app.set_offer_service(OfferService(mock_db, ai_service=mock_ai_service))
    
    # Create test client
    with app.test_client() as client:
        # Create default cost settings
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
        mock_db.save_cost_settings(settings_data)
        yield client
    
    # Restore original services
    app.set_repository(original_repo)
    app.set_offer_service(original_offer_service)

@pytest.fixture
def default_cost_settings(mock_db):
    """Create default cost settings in the mock database."""
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
    mock_db.save_cost_settings(settings_data)
    return settings_data

def test_route_calculation_endpoint(client, mock_location):
    """Test the /route endpoint for calculating routes."""
    # Prepare test data
    pickup_time = datetime.now()
    delivery_time = pickup_time + timedelta(days=1)
    
    data = {
        "origin": {
            "latitude": mock_location.latitude,
            "longitude": mock_location.longitude,
            "address": mock_location.address
        },
        "destination": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "address": "Paris, France"
        },
        "pickup_time": pickup_time.isoformat(),
        "delivery_time": delivery_time.isoformat(),
        "cargo": {
            "id": str(uuid4()),
            "type": "General",
            "weight": 15000.0,
            "value": 50000.0,
            "special_requirements": ["temperature_controlled"]
        },
        "transport_type": {
            "id": str(uuid4()),
            "name": "Standard Truck",
            "capacity": {
                "max_weight": 20000,
                "max_volume": 80.0,
                "unit": "metric"
            },
            "restrictions": []
        }
    }
    
    # Make request
    response = client.post(
        '/route',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    # Assert response
    assert response.status_code == 200
    route_data = json.loads(response.data)
    
    # Verify route structure matches spec
    assert "id" in route_data
    assert "origin" in route_data
    assert "destination" in route_data
    assert "pickup_time" in route_data
    assert "delivery_time" in route_data
    assert "empty_driving" in route_data
    assert "main_route" in route_data
    assert "timeline" in route_data
    assert "total_duration_hours" in route_data
    assert "is_feasible" in route_data
    assert "duration_validation" in route_data
    
    # Verify route details match spec
    assert route_data["is_feasible"] is True  # Always true in PoC
    assert route_data["duration_validation"] is True
    assert route_data["total_duration_hours"] > 0
    
    # Verify empty driving scenario matches spec
    empty_driving = route_data["empty_driving"]
    assert empty_driving["distance_km"] == 200.0  # Default distance
    assert empty_driving["duration_hours"] == 4.0  # Default duration
    
    # Verify main route structure
    main_route = route_data["main_route"]
    assert main_route["distance_km"] > 0
    assert main_route["duration_hours"] > 0
    assert "country_segments" in main_route
    assert len(main_route["country_segments"]) > 0
    
    # Verify timeline events
    timeline = route_data["timeline"]
    assert len(timeline) >= 2  # pickup and delivery
    event_types = [event["type"] for event in timeline]
    assert "PICKUP" in event_types
    assert "DELIVERY" in event_types

def test_cost_calculation_endpoint(client, mock_location):
    """Test the /costs endpoint for calculating costs."""
    # First create a route
    pickup_time = datetime.now()
    delivery_time = pickup_time + timedelta(days=1)
    
    route_data = {
        "origin": {
            "latitude": mock_location.latitude,
            "longitude": mock_location.longitude,
            "address": mock_location.address
        },
        "destination": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "address": "Paris, France"
        },
        "pickup_time": pickup_time.isoformat(),
        "delivery_time": delivery_time.isoformat(),
        "cargo": {
            "id": str(uuid4()),
            "type": "General",
            "weight": 15000.0,
            "value": 50000.0,
            "special_requirements": ["temperature_controlled"]
        },
        "transport_type": {
            "id": str(uuid4()),
            "name": "Standard Truck",
            "capacity": {
                "max_weight": 20000,
                "max_volume": 80.0,
                "unit": "metric"
            },
            "restrictions": []
        }
    }
    
    route_response = client.post(
        '/route',
        data=json.dumps(route_data),
        content_type='application/json'
    )
    assert route_response.status_code == 200
    route = json.loads(route_response.data)
    
    # Test costs by route ID
    response = client.post(
        f'/costs/{route["id"]}',
        data=json.dumps({"include_empty_driving": True}),
        content_type='application/json'
    )
    
    # Assert response
    assert response.status_code == 200
    cost_data = json.loads(response.data)
    
    # Verify cost breakdown structure
    assert "total_cost" in cost_data
    assert "breakdown" in cost_data
    assert cost_data["total_cost"] > 0
    
    # Verify individual cost components
    breakdown = cost_data["breakdown"]
    expected_components = [
        "fuel", "driver", "maintenance", "insurance"
    ]
    for component in expected_components:
        assert component in breakdown
        assert isinstance(breakdown[component], (int, float))
        assert breakdown[component] >= 0
    
    # Test with custom cost settings
    response = client.post(
        f'/costs/{route["id"]}',
        data=json.dumps({
            "include_empty_driving": True,
            "cost_settings": [
                {
                    "type": "fuel",
                    "category": "variable",
                    "base_value": 1.5,
                    "multiplier": 1.2,
                    "is_enabled": True,
                    "description": "Fuel cost per km"
                },
                {
                    "type": "driver",
                    "category": "fixed",
                    "base_value": 35.0,
                    "multiplier": 1.0,
                    "is_enabled": True,
                    "description": "Driver cost per hour"
                }
            ]
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_cost' in data
    assert 'breakdown' in data
    assert data['total_cost'] > 0
    breakdown = data['breakdown']
    assert 'fuel' in breakdown
    assert 'driver' in breakdown
    assert breakdown['fuel'] > 0
    assert breakdown['driver'] > 0

def test_route_calculation_invalid_input(client):
    """Test the /route endpoint with invalid input."""
    # Test with missing required fields
    data = {
        "origin": {
            "latitude": 52.5200,
            "longitude": 13.4050
            # Missing address
        }
    }
    
    response = client.post(
        '/route',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "error" in error_data

def test_route_calculation_invalid_dates(client, mock_location):
    """Test the /route endpoint with invalid dates."""
    # Prepare test data with delivery before pickup
    pickup_time = datetime.now()
    delivery_time = pickup_time - timedelta(hours=1)  # Invalid
    
    data = {
        "origin": {
            "latitude": mock_location.latitude,
            "longitude": mock_location.longitude,
            "address": mock_location.address
        },
        "destination": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "address": "Paris, France"
        },
        "pickup_time": pickup_time.isoformat(),
        "delivery_time": delivery_time.isoformat()
    }
    
    response = client.post(
        '/route',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "error" in error_data

def test_route_calculation_performance(client, mock_location):
    """Test the performance of the /route endpoint."""
    import time
    
    # Prepare test data
    pickup_time = datetime.now()
    delivery_time = pickup_time + timedelta(days=1)
    
    data = {
        "origin": {
            "latitude": mock_location.latitude,
            "longitude": mock_location.longitude,
            "address": mock_location.address
        },
        "destination": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "address": "Paris, France"
        },
        "pickup_time": pickup_time.isoformat(),
        "delivery_time": delivery_time.isoformat()
    }
    
    # Measure response time
    start_time = time.time()
    response = client.post(
        '/route',
        data=json.dumps(data),
        content_type='application/json'
    )
    end_time = time.time()
    
    # Assert response time is within acceptable range (e.g., under 500ms)
    assert end_time - start_time < 0.5
    assert response.status_code == 200

def test_list_cost_settings(client, mock_db):
    """Test listing all cost settings."""
    response = client.get('/costs/settings')
    assert response.status_code == 200
    settings = json.loads(response.data)
    assert isinstance(settings, list)
    if len(settings) > 0:
        setting = settings[0]
        assert 'id' in setting
        assert 'type' in setting
        assert 'category' in setting
        assert 'base_value' in setting
        assert 'is_enabled' in setting

def test_update_cost_setting(client, mock_db, default_cost_settings):
    """Test updating a cost setting."""
    # First get the current cost settings
    response = client.get('/costs/settings')
    assert response.status_code == 200
    current_settings = json.loads(response.data)
    assert isinstance(current_settings, list)
    assert len(current_settings) > 0
    
    # Update a cost setting
    cost_item = current_settings[0]
    update_data = [{
        "id": cost_item['id'],
        "multiplier": 1.2,
        "is_enabled": True
    }]
    
    response = client.post(
        '/costs/settings',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verify the update
    response = client.get('/costs/settings')
    assert response.status_code == 200
    updated_settings = json.loads(response.data)
    assert isinstance(updated_settings, list)
    updated_item = next(
        item for item in updated_settings 
        if item['id'] == cost_item['id']
    )
    assert updated_item['multiplier'] == 1.2
    assert updated_item['is_enabled'] == True

def test_list_historical_offers(client, mock_db):
    """Test listing historical offers."""
    response = client.get('/offers/history')
    assert response.status_code == 200
    offers = json.loads(response.data)
    assert isinstance(offers, list)
    if len(offers) > 0:
        offer = offers[0]
        assert 'id' in offer
        assert 'route_id' in offer
        assert 'total_cost' in offer
        assert 'margin' in offer
        assert 'final_price' in offer
        assert 'fun_fact' in offer
        assert 'status' in offer
        assert 'created_at' in offer
        assert 'cost_breakdown' in offer
        if 'route' in offer and offer['route']:
            route = offer['route']
            assert 'origin_address' in route
            assert 'destination_address' in route
            assert 'pickup_time' in route
            assert 'delivery_time' in route
            assert 'total_duration_hours' in route

def test_list_offers_with_filters(client, mock_db):
    """Test listing offers with various filter combinations."""
    # Setup test data
    test_offers = [
        {
            "id": str(uuid4()),
            "created_at": datetime.now() - timedelta(days=5),
            "status": "draft",
            "currency": "EUR",
            "price": 1000.0,
            "margin": 15.0,
            "route_id": str(uuid4()),
            "costs": {
                "base_cost": 800.0,
                "fuel_cost": 100.0,
                "driver_cost": 50.0,
                "maintenance_cost": 30.0,
                "additional_costs": 20.0
            }
        },
        {
            "id": str(uuid4()),
            "created_at": datetime.now() - timedelta(days=3),
            "status": "pending",
            "currency": "EUR",
            "price": 1500.0,
            "margin": 20.0,
            "route_id": str(uuid4()),
            "costs": {
                "base_cost": 1200.0,
                "fuel_cost": 150.0,
                "driver_cost": 75.0,
                "maintenance_cost": 45.0,
                "additional_costs": 30.0
            }
        },
        {
            "id": str(uuid4()),
            "created_at": datetime.now() - timedelta(days=1),
            "status": "accepted",
            "currency": "USD",
            "price": 2000.0,
            "margin": 25.0,
            "route_id": str(uuid4()),
            "costs": {
                "base_cost": 1500.0,
                "fuel_cost": 200.0,
                "driver_cost": 100.0,
                "maintenance_cost": 60.0,
                "additional_costs": 40.0
            }
        }
    ]
    
    # Save test offers to mock database
    for offer in test_offers:
        mock_db.save_offer(offer)
    
    app.logger.info("Test data setup complete. Starting filter tests...")
    
    # Test 1: Filter by date range
    response = client.get('/api/v1/offers', query_string={
        'start_date': (datetime.now() - timedelta(days=4)).isoformat(),
        'end_date': datetime.now().isoformat()
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 2  # Should only get the last 2 offers
    app.logger.info("Date range filter test passed")
    
    # Test 2: Filter by price range
    response = client.get('/api/v1/offers', query_string={
        'min_price': 1200,
        'max_price': 1800
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1  # Should only get the middle offer
    assert float(data['offers'][0]['basic_info']['final_price']) == 1500.0
    app.logger.info("Price range filter test passed")
    
    # Test 3: Filter by status
    response = client.get('/api/v1/offers', query_string={
        'status': 'pending'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1
    assert data['offers'][0]['basic_info']['status'] == 'pending'
    app.logger.info("Status filter test passed")
    
    # Test 4: Filter by currency
    response = client.get('/api/v1/offers', query_string={
        'currency': 'USD'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1
    assert data['offers'][0]['basic_info']['currency'] == 'USD'
    app.logger.info("Currency filter test passed")
    
    # Test 5: Combined filters
    response = client.get('/api/v1/offers', query_string={
        'start_date': (datetime.now() - timedelta(days=4)).isoformat(),
        'end_date': datetime.now().isoformat(),
        'min_price': 1000,
        'max_price': 2500,
        'currency': 'EUR'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1  # Should only get the middle offer
    assert data['offers'][0]['basic_info']['currency'] == 'EUR'
    assert float(data['offers'][0]['basic_info']['final_price']) == 1500.0
    app.logger.info("Combined filters test passed")
    
    # Test 6: Invalid filter values
    response = client.get('/api/v1/offers', query_string={
        'min_price': 'invalid',
        'max_price': 1000
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    app.logger.info("Invalid filter validation test passed")
    
    # Test 7: No results case
    response = client.get('/api/v1/offers', query_string={
        'min_price': 5000,
        'max_price': 6000
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 0
    app.logger.info("No results test passed")

def test_list_offers_with_settings(client, mock_db):
    """Test listing offers with applied settings included."""
    # Setup test data
    test_settings = [
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
            "multiplier": 1.2,
            "currency": "EUR",
            "is_enabled": True,
            "description": "Driver daily rate"
        }
    ]
    
    # Save settings to mock database
    mock_db.save_cost_settings(test_settings)
    
    test_offer = {
        "id": str(uuid4()),
        "created_at": datetime.now(),
        "status": "pending",
        "currency": "EUR",
        "price": 1500.0,
        "margin": 20.0,
        "route_id": str(uuid4()),
        "costs": {
            "base_cost": 1200.0,
            "fuel_cost": 150.0,
            "driver_cost": 75.0,
            "maintenance_cost": 45.0,
            "additional_costs": 30.0
        },
        "applied_settings": {
            "fuel": test_settings[0],
            "driver": test_settings[1]
        }
    }
    
    # Save test offer to mock database
    mock_db.save_offer(test_offer)
    
    app.logger.info("Test data setup complete. Starting settings inclusion test...")
    
    # Test 1: Fetch without settings
    response = client.get('/api/v1/offers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1
    assert 'applied_settings' not in data['offers'][0]
    app.logger.info("Fetch without settings test passed")
    
    # Test 2: Fetch with settings included
    response = client.get('/api/v1/offers', query_string={'include_settings': True})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['offers']) == 1
    assert 'applied_settings' in data['offers'][0]
    
    # Verify settings content
    settings = data['offers'][0]['applied_settings']
    assert 'fuel' in settings
    assert 'driver' in settings
    assert settings['fuel']['base_value'] == 1.5
    assert settings['driver']['multiplier'] == 1.2
    app.logger.info("Fetch with settings test passed")
    
    # Test 3: Verify settings format matches frontend expectations
    settings = data['offers'][0]['applied_settings']
    for setting_type, setting_data in settings.items():
        assert all(key in setting_data for key in [
            'base_value',
            'multiplier',
            'category',
            'currency',
            'description',
            'is_enabled'
        ])
    app.logger.info("Settings format verification passed")
