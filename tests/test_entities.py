import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import List, Dict
from backend.domain.entities import (
    Location, TimelineEvent, Route, MainRoute, EmptyDriving,
    CountrySegment, Cargo, TransportType, Capacity, CostItem,
    Offer, ServiceError, User, BusinessEntity, TruckDriverPair
)

def test_location_entity():
    """Test Location entity creation and field types"""
    location = Location(
        latitude=52.52,
        longitude=13.405,
        address="Berlin, Germany"
    )
    assert isinstance(location.latitude, float)
    assert isinstance(location.longitude, float)
    assert isinstance(location.address, str)

def test_timeline_event_entity():
    """Test TimelineEvent entity creation and field types"""
    location = Location(52.52, 13.405, "Berlin")
    event = TimelineEvent(
        event_type="pickup",
        location=location,
        planned_time=datetime.now(UTC),
        duration_minutes=30,
        description="Pickup cargo",
        is_required=True
    )
    assert event.event_type in ["start", "pickup", "rest", "border", "delivery", "end"]
    assert isinstance(event.location, Location)
    assert isinstance(event.planned_time, datetime)
    assert isinstance(event.duration_minutes, int)
    assert isinstance(event.is_required, bool)

def test_transport_entities():
    """Test transport-related entities"""
    # Test Capacity
    capacity = Capacity(
        max_weight=20.0,
        max_volume=40.0,
        unit="metric"
    )
    assert isinstance(capacity.max_weight, float)
    assert isinstance(capacity.max_volume, float)
    
    # Test TransportType
    transport = TransportType(
        id=uuid4(),
        name="Heavy Truck",
        capacity=capacity,
        restrictions=["ADR", "Temperature controlled"]
    )
    assert isinstance(transport.id, UUID)
    assert isinstance(transport.restrictions, list)
    
    # Test TruckDriverPair
    pair = TruckDriverPair(
        id=uuid4(),
        truck_type="Heavy Truck",
        driver_id="D123",
        capacity=20.0,
        availability=True
    )
    assert isinstance(pair.id, UUID)
    assert isinstance(pair.availability, bool)

def test_route_related_entities():
    """Test route and its related entities"""
    # Test CountrySegment
    segment = CountrySegment(
        country="Germany",
        distance_km=500.0,
        duration_hours=6.0
    )
    assert isinstance(segment.distance_km, float)
    
    # Test EmptyDriving
    empty = EmptyDriving(
        distance_km=200.0,
        duration_hours=4.0,
        base_cost=100.0
    )
    assert empty.distance_km == 200.0  # Default value
    assert empty.duration_hours == 4.0  # Default value
    
    # Test MainRoute
    main_route = MainRoute(
        distance_km=1000.0,
        duration_hours=12.0,
        country_segments=[segment]
    )
    assert isinstance(main_route.country_segments, list)
    
    # Test Route
    route = Route(
        id=uuid4(),
        origin=Location(52.52, 13.405, "Berlin"),
        destination=Location(48.85, 2.35, "Paris"),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC),
        empty_driving=empty,
        main_route=main_route,
        timeline=[],
        total_duration_hours=16.0,
        is_feasible=True,
        duration_validation=True
    )
    assert isinstance(route.id, UUID)
    assert isinstance(route.origin, Location)
    assert isinstance(route.is_feasible, bool)

def test_business_entities():
    """Test business-related entities"""
    # Test Cargo
    cargo = Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,
        value=50000.0,
        special_requirements=["Temperature controlled"]
    )
    assert isinstance(cargo.weight, float)
    assert isinstance(cargo.special_requirements, list)
    
    # Test CostItem
    cost = CostItem(
        id=uuid4(),
        type="fuel",
        category="variable",
        base_value=1.5,
        description="Fuel cost per km",
        multiplier=1.0,
        currency="EUR"
    )
    assert cost.type == "fuel"
    assert cost.category == "variable"
    assert cost.base_value == 1.5
    assert cost.currency == "EUR"
    
    # Test Offer
    offer = Offer(
        id=uuid4(),
        route_id=uuid4(),
        total_cost=1000.0,
        margin=0.2,
        final_price=1200.0,
        fun_fact="This route crosses 3 countries!",
        status="pending",
        created_at=datetime.now(UTC),
        cost_breakdown={"fuel": 500.0, "driver": 500.0}
    )
    assert isinstance(offer.cost_breakdown, dict)
    assert isinstance(offer.margin, float)

def test_user_entities():
    """Test user-related entities"""
    # Test User
    user = User(
        id=uuid4(),
        name="John Doe",
        role="transport_manager",
        permissions=["full_access"]
    )
    assert user.role == "transport_manager"
    assert "full_access" in user.permissions
    
    # Test BusinessEntity
    business = BusinessEntity(
        id=uuid4(),
        name="Logistics Corp",
        type="carrier",
        operating_countries=["Germany", "France"]
    )
    assert isinstance(business.operating_countries, list)

def test_service_error():
    """Test ServiceError entity"""
    error = ServiceError(
        code="ROUTE_001",
        message="Invalid route parameters",
        details={"field": "pickup_time", "issue": "in the past"},
        timestamp=datetime.now(UTC)
    )
    assert isinstance(error.details, dict)
    assert isinstance(error.timestamp, datetime)

def test_cost_setting():
    # Test CostItem
    cost = CostItem(
        id=uuid4(),
        type="fuel",
        category="variable",
        base_value=1.5,
        description="Fuel cost per km",
        multiplier=1.0,
        currency="EUR"
    )
    
    assert cost.type == "fuel"
    assert cost.category == "variable"
    assert cost.base_value == 1.5
    assert cost.currency == "EUR"
