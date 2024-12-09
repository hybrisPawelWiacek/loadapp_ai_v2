import pytest
from datetime import datetime, timedelta
import pytz

from backend.domain.services import RoutePlanningService
from backend.domain.entities import Location, TransportType, Cargo, TimelineEvent

def test_calculate_route_basic(mock_location):
    """Test basic route calculation with minimal inputs."""
    service = RoutePlanningService()
    
    # Test data with timezone-aware datetimes
    tz = pytz.timezone('Europe/Berlin')
    pickup_time = datetime.now(tz)
    delivery_time = pickup_time + timedelta(days=1)
    
    # Calculate route
    route = service.calculate_route(
        origin=mock_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Assertions
    assert route is not None
    assert route.origin == mock_location
    assert route.pickup_time == pickup_time
    assert route.delivery_time == delivery_time
    assert route.is_feasible is True
    assert route.duration_validation is True
    
    # Verify timeline structure
    assert isinstance(route.timeline, list)
    assert all(isinstance(event, TimelineEvent) for event in route.timeline)

def test_calculate_route_with_cargo(mock_location, mock_cargo):
    """Test route calculation with cargo details."""
    service = RoutePlanningService()
    
    # Calculate route
    tz = pytz.timezone('Europe/Berlin')
    pickup_time = datetime.now(tz)
    delivery_time = pickup_time + timedelta(days=1)
    route = service.calculate_route(
        origin=mock_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        cargo=mock_cargo
    )
    
    # Assertions
    assert route is not None
    assert route.empty_driving is not None
    assert route.empty_driving.distance_km == 200.0  # Default value
    assert route.empty_driving.duration_hours == 4.0  # Default value
    assert len(route.timeline) >= 2  # At least start and end events

def test_calculate_route_with_transport_type(mock_location, mock_transport_type):
    """Test route calculation with transport type."""
    service = RoutePlanningService()
    
    # Calculate route
    tz = pytz.timezone('Europe/Berlin')
    pickup_time = datetime.now(tz)
    delivery_time = pickup_time + timedelta(days=1)
    route = service.calculate_route(
        origin=mock_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        transport_type=mock_transport_type
    )
    
    # Assertions
    assert route is not None
    assert route.main_route is not None
    assert len(route.main_route.country_segments) > 0
    assert route.total_duration_hours > 0

def test_calculate_route_timeline_validation(mock_location):
    """Test comprehensive route calculation timeline validation."""
    service = RoutePlanningService()
    tz = pytz.timezone('Europe/Berlin')
    base_time = datetime.now(tz)
    
    # Test case 1: Delivery before pickup
    with pytest.raises(ValueError, match="Delivery time must be after pickup"):
        service.calculate_route(
            origin=mock_location,
            destination=Location(latitude=48.8566, longitude=2.3522, address="Paris"),
            pickup_time=base_time,
            delivery_time=base_time - timedelta(hours=1)
        )
    
    # Test case 2: Exceeding maximum daily driving time (9 hours in EU)
    with pytest.raises(ValueError, match="Exceeds maximum daily driving time"):
        service.calculate_route(
            origin=mock_location,
            destination=Location(latitude=41.9028, longitude=12.4964, address="Rome"),
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=10)  # Too short for the distance
        )
    
    # Test case 3: Missing required rest period
    with pytest.raises(ValueError, match="Required rest period not possible"):
        service.calculate_route(
            origin=mock_location,
            destination=Location(latitude=40.4168, longitude=-3.7038, address="Madrid"),
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=20)  # Not enough time for rest
        )
    
    # Test case 4: Invalid loading time window (too early)
    early_morning = base_time.replace(hour=3, minute=0)
    with pytest.raises(ValueError, match="Loading time outside of allowed window"):
        service.calculate_route(
            origin=mock_location,
            destination=Location(latitude=52.5200, longitude=13.4050, address="Berlin"),
            pickup_time=early_morning,
            delivery_time=early_morning + timedelta(hours=5)
        )

def test_timeline_events_structure(mock_location):
    """Test the structure and completeness of timeline events."""
    service = RoutePlanningService()
    tz = pytz.timezone('Europe/Berlin')
    pickup_time = datetime.now(tz)
    delivery_time = pickup_time + timedelta(days=1)
    
    route = service.calculate_route(
        origin=mock_location,
        destination=Location(latitude=48.8566, longitude=2.3522, address="Paris"),
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Verify timeline events
    assert len(route.timeline) >= 4  # Should have at least: start, pickup, rest, delivery
    
    # Verify event sequence
    event_types = [event.event_type for event in route.timeline]
    assert event_types[0] == "start"
    assert event_types[1] == "pickup"
    assert "rest" in event_types[2:-1]  # Rest should be between pickup and delivery
    assert event_types[-1] == "delivery"
    
    # Verify time sequence
    for i in range(len(route.timeline) - 1):
        assert route.timeline[i].time < route.timeline[i + 1].time
        
    # Verify location data
    for event in route.timeline:
        assert isinstance(event.location, Location)
        assert hasattr(event.location, 'latitude')
        assert hasattr(event.location, 'longitude')
        assert hasattr(event.location, 'address')

def test_calculate_route_complete(mock_location, mock_transport_type, mock_cargo):
    """Test route calculation with all optional parameters."""
    service = RoutePlanningService()
    
    # Calculate route
    tz = pytz.timezone('Europe/Berlin')
    pickup_time = datetime.now(tz)
    delivery_time = pickup_time + timedelta(days=1)
    route = service.calculate_route(
        origin=mock_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        transport_type=mock_transport_type,
        cargo=mock_cargo
    )
    
    # Assertions
    assert route is not None
    assert route.empty_driving is not None
    assert route.main_route is not None
    assert len(route.timeline) >= 2
    assert route.is_feasible is True
    assert route.duration_validation is True
    assert route.total_duration_hours > 0
