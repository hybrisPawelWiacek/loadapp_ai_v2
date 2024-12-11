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
def mock_repository():
    return Mock()

@pytest.fixture
def mock_cost_settings_repository():
    return Mock()

@pytest.fixture
def mock_cost_calculation_service():
    return Mock()

@pytest.fixture
def mock_cost_validator():
    return Mock()

@pytest.fixture
def mock_metrics_service():
    return Mock()

@pytest.fixture
def route_service(
    mock_repository,
    mock_cost_settings_repository,
    mock_cost_calculation_service,
    mock_cost_validator,
    mock_metrics_service
):
    return RouteService(
        repository=mock_repository,
        cost_settings_repository=mock_cost_settings_repository,
        cost_calculation_service=mock_cost_calculation_service,
        cost_validator=mock_cost_validator,
        metrics_service=mock_metrics_service
    )

@pytest.fixture
def sample_route():
    return Route(
        id=str(uuid4()),
        origin=Location(latitude=52.52, longitude=13.405, address="Berlin"),
        destination=Location(latitude=48.85, longitude=2.35, address="Paris"),
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
    return [
        CostSetting(
            id=str(uuid4()),
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True
        ),
        CostSetting(
            id=str(uuid4()),
            type="driver",
            category="fixed",
            base_value=200.0,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True
        )
    ]

def test_create_route_success(route_service, sample_route, sample_cost_settings, mock_cost_calculation_service):
    """Test successful route creation with cost calculation."""
    # Setup
    mock_cost_calculation_service.calculate_route_cost.return_value = {
        "total_cost": 1500.0,
        "currency": "EUR",
        "cost_breakdown": {"base": 1000.0, "variable": 500.0},
        "optimization_insights": {"potential_savings": 100.0}
    }

    # Execute
    result = route_service.create_route(sample_route, sample_cost_settings)

    # Verify
    assert result.total_cost == 1500.0
    assert result.currency == "EUR"
    assert result.cost_breakdown == {"base": 1000.0, "variable": 500.0}
    assert result.optimization_insights == {"potential_savings": 100.0}
    assert len(result.timeline_events) > 0
    assert result.has_rest_stops is True

def test_create_route_with_rest_stops(route_service, sample_route, sample_cost_settings):
    """Test route creation with automatic rest stop calculation."""
    # Execute
    result = route_service.create_route(sample_route, sample_cost_settings, validate_timeline=True)

    # Verify
    rest_stops = [event for event in result.timeline_events if event.type == "rest"]
    assert len(rest_stops) == route_service._calculate_required_rest_stops(14.5)  # 14.5 hours total duration
    assert result.total_rest_duration == len(rest_stops) * route_service.MIN_REST_DURATION_HOURS

def test_create_route_validation_error(route_service, sample_route, sample_cost_settings):
    """Test route creation with validation errors."""
    # Modify route to make it invalid (too short delivery time)
    sample_route.delivery_time = sample_route.pickup_time + timedelta(hours=2)

    # Execute and verify
    with pytest.raises(RouteValidationException) as exc_info:
        route_service.create_route(sample_route, sample_cost_settings)
    assert "delivery time too early" in str(exc_info.value).lower()

def test_loading_window_validation(route_service, sample_route):
    """Test validation of loading window constraints."""
    # Test pickup time outside loading window (3 AM)
    invalid_pickup_time = datetime.now(UTC).replace(hour=3, minute=0)
    sample_route.pickup_time = invalid_pickup_time
    
    assert not route_service._is_within_loading_window(invalid_pickup_time)

    # Test pickup time within loading window (10 AM)
    valid_pickup_time = datetime.now(UTC).replace(hour=10, minute=0)
    sample_route.pickup_time = valid_pickup_time
    
    assert route_service._is_within_loading_window(valid_pickup_time)

def test_rest_stop_calculation(route_service):
    """Test calculation of required rest stops."""
    # Test no rest stops needed
    assert route_service._calculate_required_rest_stops(4.0) == 0

    # Test one rest stop needed
    assert route_service._calculate_required_rest_stops(6.0) == 1

    # Test multiple rest stops needed
    assert route_service._calculate_required_rest_stops(15.0) == 3

def test_calculate_rest_stops_timeline(route_service, sample_route):
    """Test generation of timeline events with rest stops."""
    # Execute
    timeline = route_service._calculate_rest_stops(sample_route)

    # Verify
    assert len(timeline) > 0
    event_types = [event.type for event in timeline]
    assert "start" in event_types
    assert "pickup" in event_types
    assert "rest" in event_types
    assert "delivery" in event_types
    assert "end" in event_types

    # Verify event order and timing
    events = sorted(timeline, key=lambda x: x.time)
    for i in range(len(events) - 1):
        assert events[i].time < events[i + 1].time

def test_metrics_tracking(route_service, sample_route, sample_cost_settings, mock_metrics_service):
    """Test metrics tracking during route creation."""
    # Setup
    mock_metrics_service.counter = Mock()

    # Execute
    route_service.create_route(sample_route, sample_cost_settings)

    # Verify
    mock_metrics_service.counter.assert_called_with(
        "route.creation.success",
        labels={
            "has_cost_settings": "True",
            "route_type": "unknown"
        }
    )

def test_route_with_special_transport_type(route_service, sample_route, sample_cost_settings):
    """Test route creation with special transport type requirements."""
    # Setup
    sample_route.transport_type = TransportType(
        id=str(uuid4()),
        name="SPECIAL_TRUCK",
        restrictions=["ADR", "Temperature controlled"]
    )

    # Execute
    result = route_service.create_route(sample_route, sample_cost_settings)

    # Verify
    assert result.transport_type.restrictions == ["ADR", "Temperature controlled"]
    rest_stops = [event for event in result.timeline_events if event.type == "rest"]
    assert len(rest_stops) > 0  # Special transport requires more frequent stops 