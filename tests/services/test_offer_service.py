import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import UUID
from backend.services.offer_service import OfferService
from backend.services.cost_calculation_service import CostCalculationService
from backend.domain.entities import Route, MainRoute, Location, Offer

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def mock_cost_service():
    return Mock()

@pytest.fixture
def offer_service(mock_repository, mock_cost_service):
    return OfferService(mock_repository, mock_cost_service)

@pytest.fixture
def sample_route():
    return Route(
        id="test-route-id",
        origin=Location(latitude=52.52, longitude=13.405, address="Berlin"),
        destination=Location(latitude=48.8566, longitude=2.3522, address="Paris"),
        main_route=MainRoute(
            distance=1000000,  # 1000 km in meters
            duration=36000,    # 10 hours in seconds
            polyline="test_polyline"
        ),
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow(),
        total_cost=1000.0,
        currency="EUR"
    )

@pytest.fixture
def sample_costs():
    return {
        'total_cost': 1000.0,
        'breakdown': {
            'base_cost': 300.0,
            'distance_cost': 500.0,
            'time_cost': 200.0,
            'fuel_cost': 300.0,
            'driver_cost': 200.0,
            'toll_cost': 100.0,
            'maintenance_cost': 100.0,
            'insurance_cost': 200.0,
            'overhead_cost': 100.0
        }
    }

def test_create_offer_success(offer_service, mock_repository, mock_cost_service, sample_route, sample_costs):
    # Setup
    route_id = "test-route-id"
    margin = 15.0
    mock_repository.get_route.return_value = sample_route
    mock_cost_service.calculate_costs.return_value = sample_costs
    
    # Mock the save_offer to return an offer with a known ID
    def mock_save_offer(offer):
        offer.id = "test-offer-id"
        return offer
    mock_repository.save_offer.side_effect = mock_save_offer

    # Execute
    result = offer_service.create_offer(route_id, margin)

    # Verify
    assert result is not None
    assert result['id'] == "test-offer-id"
    assert result['route_id'] == route_id
    assert result['base_cost'] == 1000.0
    assert result['margin_percentage'] == 15.0
    assert result['total_price'] == 1150.0  # 1000 * (1 + 15%)
    assert result['cost_breakdown'] == sample_costs['breakdown']
    assert result['status'] == "pending"
    assert result['currency'] == "EUR"

    # Verify repository calls
    mock_repository.get_route.assert_called_once_with(route_id)
    mock_repository.save_offer.assert_called_once()

def test_create_offer_invalid_margin(offer_service):
    # Test with invalid margin
    with pytest.raises(ValueError) as exc_info:
        offer_service.create_offer("test-route-id", margin=150.0)
    assert "Margin must be between 0 and 100" in str(exc_info.value)

def test_create_offer_route_not_found(offer_service, mock_repository):
    # Setup
    mock_repository.get_route.return_value = None

    # Test with non-existent route
    with pytest.raises(ValueError) as exc_info:
        offer_service.create_offer("non-existent-route", margin=15.0)
    assert "Route with ID non-existent-route not found" in str(exc_info.value)

def test_create_offer_cost_calculation_failure(offer_service, mock_repository, mock_cost_service, sample_route):
    # Setup
    route_id = "test-route-id"
    mock_repository.get_route.return_value = sample_route
    mock_cost_service.calculate_costs.side_effect = Exception("Cost calculation failed")

    # Execute
    result = offer_service.create_offer(route_id)

    # Verify
    assert result is None
    mock_repository.get_route.assert_called_once_with(route_id)
    mock_cost_service.calculate_costs.assert_called_once()

def test_create_offer_with_existing_costs(offer_service, mock_repository, sample_route, sample_costs):
    # Setup
    route_id = "test-route-id"
    sample_route.cost_breakdown = sample_costs['breakdown']
    mock_repository.get_route.return_value = sample_route
    
    # Mock the save_offer to return an offer with a known ID
    def mock_save_offer(offer):
        offer.id = "test-offer-id"
        return offer
    mock_repository.save_offer.side_effect = mock_save_offer

    # Execute
    result = offer_service.create_offer(route_id)

    # Verify
    assert result is not None
    assert result['cost_breakdown'] == sample_costs['breakdown']
    # Cost service should not be called since costs already exist
    mock_cost_service.calculate_costs.assert_not_called()
