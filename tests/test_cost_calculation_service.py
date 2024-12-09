from datetime import datetime, UTC
import pytest
from uuid import uuid4

from backend.domain.services.cost_calculation_service import CostCalculationService
from backend.domain.entities import (
    Route, Location, EmptyDriving, MainRoute, CountrySegment,
    CostSetting, Cargo
)

@pytest.fixture
def service():
    return CostCalculationService()

@pytest.fixture
def mock_route():
    # Create a mock route for testing
    origin = Location(52.52, 13.405, "Berlin, Germany")
    destination = Location(52.237, 21.017, "Warsaw, Poland")
    
    empty_driving = EmptyDriving(
        distance_km=50.0,
        duration_hours=1.0,
        base_cost=75.0
    )
    
    main_route = MainRoute(
        distance_km=700.0,
        duration_hours=9.0,
        country_segments=[
            CountrySegment(
                country="Germany",
                distance_km=300.0,
                duration_hours=4.0
            ),
            CountrySegment(
                country="Poland",
                distance_km=400.0,
                duration_hours=5.0
            )
        ]
    )
    
    return Route(
        id=uuid4(),
        origin=origin,
        destination=destination,
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC),
        empty_driving=empty_driving,
        main_route=main_route,
        timeline=[],  # Not relevant for cost calculation
        total_duration_hours=10.0,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def mock_cargo():
    return Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,  # kg
        value=150000.0,  # EUR (high-value cargo)
        special_requirements=["ADR", "Temperature controlled"]
    )

def test_basic_cost_breakdown(service, mock_route):
    """Test basic cost breakdown without cargo"""
    costs = service.calculate_total_cost(mock_route)
    
    # Required cost components
    required_components = {
        "fuel", "driver", "toll", "maintenance",
        "insurance", "overhead", "empty_driving", "total"
    }
    assert all(component in costs for component in required_components)
    
    # Verify no cargo-specific costs
    cargo_components = {"adr_surcharge", "refrigeration", "high_value_insurance"}
    assert not any(component in costs for component in cargo_components)

def test_cost_calculations_without_cargo(service, mock_route):
    """Test cost calculations with exact values"""
    costs = service.calculate_total_cost(mock_route)
    
    total_distance = mock_route.main_route.distance_km + mock_route.empty_driving.distance_km
    total_duration = mock_route.total_duration_hours
    days = (total_duration + 23) // 24  # Round up to full days
    
    # Test each cost component
    assert costs["fuel"] == pytest.approx(total_distance * service._base_rates["fuel"])
    assert costs["driver"] == pytest.approx(total_duration * service._base_rates["driver"])
    assert costs["toll"] == pytest.approx(total_distance * service._base_rates["toll"])
    assert costs["maintenance"] == pytest.approx(total_distance * service._base_rates["maintenance"])
    assert costs["insurance"] == pytest.approx(days * service._base_rates["insurance"])
    assert costs["overhead"] == pytest.approx(days * service._base_rates["overhead"])
    assert costs["empty_driving"] == pytest.approx(mock_route.empty_driving.base_cost)

def test_cargo_specific_costs(service, mock_route, mock_cargo):
    """Test cost calculations with cargo-specific requirements"""
    costs = service.calculate_total_cost(mock_route, mock_cargo)
    
    total_distance = mock_route.main_route.distance_km + mock_route.empty_driving.distance_km
    days = (mock_route.total_duration_hours + 23) // 24
    
    # Test ADR surcharge
    assert "adr_surcharge" in costs
    assert costs["adr_surcharge"] == pytest.approx(
        total_distance * service._base_rates["adr_surcharge"]
    )
    
    # Test temperature control costs
    assert "refrigeration" in costs
    assert costs["refrigeration"] == pytest.approx(
        total_distance * service._base_rates["refrigeration"]
    )
    
    # Test high-value cargo insurance
    assert "high_value_insurance" in costs
    assert costs["high_value_insurance"] == pytest.approx(
        mock_cargo.value * service._base_rates["high_value"] * days
    )

def test_country_specific_costs(service, mock_route):
    """Test country-specific cost calculations"""
    costs = service.calculate_total_cost(mock_route)
    
    # Calculate expected costs for Germany
    germany_segment = mock_route.main_route.country_segments[0]
    expected_germany_costs = germany_segment.distance_km * 0.25 + 50.0  # toll + permit
    
    # Calculate expected costs for Poland
    poland_segment = mock_route.main_route.country_segments[1]
    expected_poland_costs = poland_segment.distance_km * 0.15 + 30.0  # toll + permit
    
    assert costs["germany_costs"] == pytest.approx(expected_germany_costs)
    assert costs["poland_costs"] == pytest.approx(expected_poland_costs)

def test_total_cost_validation(service, mock_route, mock_cargo):
    """Test that total cost is correctly calculated"""
    costs = service.calculate_total_cost(mock_route, mock_cargo)
    
    # Calculate total manually
    manual_total = sum(
        value for key, value in costs.items()
        if key != "total"
    )
    
    assert costs["total"] == pytest.approx(manual_total)
    assert costs["total"] > 0

def test_cost_items_structure(service):
    """Test that cost items have correct structure"""
    items = service.get_cost_items()
    
    for item in items:
        assert isinstance(item, CostSetting)
        assert item.id is not None
        assert item.type in service._base_rates
        assert item.base_value == service._base_rates[item.type]
        assert item.currency == "EUR"
        assert isinstance(item.description, str)
        assert item.is_enabled is True

def test_edge_cases(service, mock_route):
    """Test edge cases and potential error conditions"""
    # Test with None cargo (should not raise exception)
    costs = service.calculate_total_cost(mock_route, None)
    assert isinstance(costs, dict)
    
    # Test with cargo without special requirements
    basic_cargo = Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,
        value=1000.0,  # Low value
        special_requirements=[]
    )
    costs = service.calculate_total_cost(mock_route, basic_cargo)
    assert "adr_surcharge" not in costs
    assert "refrigeration" not in costs
    assert "high_value_insurance" not in costs
