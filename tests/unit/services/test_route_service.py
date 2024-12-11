import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4
from pytz import UTC

from backend.domain.services.route_service import RouteService
from backend.domain.entities import (
    Route, Location, TransportType, Cargo, EmptyDriving, MainRoute,
    TimelineEvent, CountrySegment, CostSetting
)
from backend.domain.exceptions import RouteValidationException

@pytest.fixture
def mock_location():
    """Create a mock location."""
    return Location(
        latitude=52.52,
        longitude=13.405,
        address="Berlin, Germany"
    )

@pytest.fixture
def sample_route(mock_location):
    """Create a sample route for testing."""
    return Route(
        id=str(uuid4()),
        origin=mock_location,
        destination=Location(
            latitude=48.85,
            longitude=2.35,
            address="Paris, France"
        ),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(days=1),
        empty_driving=EmptyDriving(
            distance_km=200.0,
            duration_hours=4.0,
            base_cost=100.0,
            country_segments=[
                CountrySegment(country="DE", distance_km=200.0, duration_hours=4.0)
            ]
        ),
        main_route=MainRoute(
            distance_km=1050.0,
            duration_hours=10.5,
            country_segments=[
                CountrySegment(country="DE", distance_km=500.0, duration_hours=5.0),
                CountrySegment(country="FR", distance_km=550.0, duration_hours=5.5)
            ]
        ),
        total_duration_hours=14.5,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def sample_cost_settings():
    """Create sample cost settings."""
    return [
        CostSetting(
            id=str(uuid4()),
            name="Fuel Cost",
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Cost per kilometer for fuel"
        ),
        CostSetting(
            id=str(uuid4()),
            name="Driver Cost",
            type="driver",
            category="fixed",
            base_value=200.0,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Fixed cost for driver per route"
        )
    ]

def test_create_route_success(route_service, sample_route, sample_cost_settings):
    """Test successful route creation with cost calculation."""
    # Execute
    result = route_service.create_route(sample_route, sample_cost_settings)

    # Verify
    assert result.total_duration_hours == 14.5
    assert result.is_feasible is True
    assert result.duration_validation is True
    assert len(result.timeline_events) > 0

def test_create_route_with_rest_stops(route_service, sample_route, sample_cost_settings):
    """Test route creation with automatic rest stop calculation."""
    # Execute
    result = route_service.create_route(sample_route, sample_cost_settings, validate_timeline=True)

    # Verify
    rest_stops = [event for event in result.timeline_events if event.event_type == "rest"]
    assert len(rest_stops) == route_service._calculate_required_rest_stops(14.5)  # 14.5 hours total duration
    assert result.total_duration_hours == 14.5 + len(rest_stops) * route_service.MIN_REST_DURATION_HOURS

def test_create_route_validation_error(route_service, sample_route, sample_cost_settings):
    """Test route creation with validation error."""
    # Modify route to be invalid
    sample_route.pickup_time = datetime.now(UTC) + timedelta(days=1)
    sample_route.delivery_time = datetime.now(UTC)  # Delivery before pickup

    # Execute and verify
    with pytest.raises(RouteValidationException):
        route_service.create_route(sample_route, sample_cost_settings)

def test_metrics_tracking(route_service, sample_route, sample_cost_settings):
    """Test metrics are tracked during route operations."""
    # Execute
    route_service.create_route(sample_route, sample_cost_settings)

    # Verify metrics were tracked
    route_service.metrics_service.counter.assert_called_with(
        "route.created",
        labels={
            "is_feasible": True,
            "has_rest_stops": True,
            "duration_validation": True
        }
    )