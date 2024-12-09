import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from backend.domain.services.route_planning_service import RoutePlanningService
from backend.domain.entities import Location, Cargo, TransportType, Capacity

def test_calculate_route_success():
    # Arrange
    service = RoutePlanningService()
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    destination = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    pickup_time = datetime.now() + timedelta(days=1)
    delivery_time = pickup_time + timedelta(days=1)
    
    # Create cargo and transport type with proper structure
    transport_type = TransportType(
        id=uuid4(),
        name="TRUCK",
        capacity=Capacity(max_weight=24000, max_volume=80, unit="metric"),
        restrictions=[]
    )
    cargo = Cargo(
        id=uuid4(),
        type="general",
        weight=1000,
        value=5000.0,
        special_requirements=[]
    )

    # Act
    route = service.calculate_route(
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        cargo=cargo,
        transport_type=transport_type
    )

    # Assert
    assert route is not None
    assert route.id is not None
    assert route.origin == origin
    assert route.destination == destination
    assert route.pickup_time == pickup_time
    assert route.delivery_time == delivery_time
    assert route.empty_driving is not None
    assert route.main_route is not None
    assert len(route.timeline) == 4  # start, pickup, rest, delivery
    assert route.total_duration_hours == route.empty_driving.duration_hours + route.main_route.duration_hours
    assert route.is_feasible is True

def test_calculate_route_invalid_delivery_time():
    # Arrange
    service = RoutePlanningService()
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    destination = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    pickup_time = datetime.now() + timedelta(days=1)
    delivery_time = pickup_time - timedelta(hours=1)  # Invalid: delivery before pickup

    # Act & Assert
    with pytest.raises(ValueError, match="Delivery time must be after pickup time"):
        service.calculate_route(
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time
        )

def test_calculate_route_timeline_events():
    # Arrange
    service = RoutePlanningService()
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    destination = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    pickup_time = datetime.now() + timedelta(days=1)
    delivery_time = pickup_time + timedelta(days=1)

    # Act
    route = service.calculate_route(
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )

    # Assert
    assert len(route.timeline) == 4
    events = {event.event_type: event for event in route.timeline}
    
    assert "start" in events
    assert "pickup" in events
    assert "rest" in events
    assert "delivery" in events
    
    assert events["start"].time == pickup_time - timedelta(hours=1)
    assert events["pickup"].time == pickup_time
    assert events["delivery"].time == delivery_time
