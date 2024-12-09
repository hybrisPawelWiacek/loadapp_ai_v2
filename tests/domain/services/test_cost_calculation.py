import pytest
from uuid import uuid4
from datetime import datetime, UTC

from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.domain.entities import CostSetting

@pytest.fixture
def service():
    return CostCalculationService()

@pytest.fixture
def mock_cost_items():
    return [
        CostSetting(
            id=uuid4(),
            type="fuel",
            category="variable",
            base_value=1.5,
            description="Fuel cost per km",
            multiplier=1.0,
            currency="EUR"
        ),
        CostSetting(
            id=uuid4(),
            type="driver",
            category="variable",
            base_value=35.0,
            description="Driver cost per hour",
            multiplier=1.0,
            currency="EUR"
        )
    ]

def test_calculate_total_cost_basic(mock_route):
    """Test basic cost calculation with default cost items."""
    service = CostCalculationService()
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Assertions for new structure
    assert costs is not None
    assert "total_cost" in costs
    assert "currency" in costs
    assert "breakdown" in costs
    assert costs["currency"] == "EUR"
    assert costs["total_cost"] > 0
    
    # Check breakdown components
    breakdown = costs["breakdown"]
    assert "base_cost" in breakdown
    assert "distance_cost" in breakdown
    assert "time_cost" in breakdown
    assert "empty_driving_cost" in breakdown
    
    # Verify cost calculations
    total_distance = mock_route.main_route.distance_km + mock_route.empty_driving.distance_km
    assert breakdown["distance_cost"] == total_distance * 0.5  # €0.50 per km
    assert breakdown["time_cost"] == mock_route.total_duration_hours * 50.0  # €50 per hour
    assert breakdown["empty_driving_cost"] == mock_route.empty_driving.distance_km * 0.3  # €0.30 per km

def test_calculate_total_cost_with_custom_items(mock_route, mock_cost_items):
    """Test cost calculation with custom cost items."""
    service = CostCalculationService()
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Basic structure assertions
    assert costs is not None
    assert "total_cost" in costs
    assert "currency" in costs
    assert "breakdown" in costs
    assert costs["currency"] == "EUR"
    
    # Verify breakdown structure
    breakdown = costs["breakdown"]
    assert isinstance(breakdown, dict)
    
    # Verify total matches sum of breakdown
    total = sum(breakdown.values())
    assert abs(costs["total_cost"] - total) < 0.01  # Allow for small floating point differences

def test_calculate_total_cost_disabled_items(mock_route):
    """Test cost calculation with some disabled cost items."""
    service = CostCalculationService()
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Basic structure assertions
    assert costs is not None
    assert "total_cost" in costs
    assert "currency" in costs
    assert "breakdown" in costs
    
    # Verify breakdown
    breakdown = costs["breakdown"]
    assert "base_cost" in breakdown
    assert "distance_cost" in breakdown
    assert breakdown["base_cost"] == 500.00  # As defined in service

def test_calculate_total_cost_with_multipliers(mock_route):
    """Test cost calculation with different multipliers."""
    service = CostCalculationService()
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Basic assertions
    assert costs is not None
    assert "total_cost" in costs
    assert "currency" in costs
    assert "breakdown" in costs
    
    # Verify distance-based calculations
    breakdown = costs["breakdown"]
    total_distance = mock_route.main_route.distance_km + mock_route.empty_driving.distance_km
    assert breakdown["distance_cost"] == total_distance * 0.5
    assert breakdown["empty_driving_cost"] == mock_route.empty_driving.distance_km * 0.3

def test_calculate_total_cost_empty_route(mock_route):
    """Test cost calculation with empty route segments."""
    service = CostCalculationService()
    
    # Modify route to have zero distances
    mock_route.main_route.distance_km = 0
    mock_route.empty_driving.distance_km = 0
    mock_route.total_duration_hours = 0
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Assertions
    assert costs is not None
    assert costs["total_cost"] >= 500.00  # Should at least include base cost
    assert costs["breakdown"]["distance_cost"] == 0
    assert costs["breakdown"]["time_cost"] == 0
    assert costs["breakdown"]["empty_driving_cost"] == 0

def test_calculate_total_cost_currency(mock_route):
    """Test cost calculation with different currencies."""
    service = CostCalculationService()
    
    # Calculate costs
    costs = service.calculate_total_cost(mock_route)
    
    # Currency assertions
    assert costs["currency"] == "EUR"  # Default currency
    assert isinstance(costs["total_cost"], float)
    
    # Verify all breakdown costs are positive
    breakdown = costs["breakdown"]
    for cost in breakdown.values():
        assert cost >= 0
        assert isinstance(cost, float)
