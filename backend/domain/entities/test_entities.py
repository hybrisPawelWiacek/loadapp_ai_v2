from datetime import datetime
from uuid import uuid4
from . import (
    Location, TimelineEvent, Route, MainRoute, EmptyDriving,
    CountrySegment, Cargo, TransportType, Capacity, CostSetting, Offer
)

def test_entity_creation():
    # Create a Location
    location = Location(
        latitude=52.52,
        longitude=13.405,
        address="Berlin, Germany"
    )

    # Create a TimelineEvent
    event = TimelineEvent(
        event_type="pickup",
        location=location,
        planned_time=datetime.now(),
        duration_minutes=30,
        description="Pickup cargo",
        is_required=True
    )

    # Create CountrySegment
    segment = CountrySegment(
        country="Germany",
        distance_km=500.0,
        duration_hours=6.0
    )

    # Create EmptyDriving
    empty_driving = EmptyDriving()  # Using defaults

    # Create MainRoute
    main_route = MainRoute(
        distance_km=1000.0,
        duration_hours=12.0,
        country_segments=[segment]
    )

    # Create Route
    route = Route(
        id=uuid4(),
        origin=location,
        destination=location,
        pickup_time=datetime.now(),
        delivery_time=datetime.now(),
        empty_driving=empty_driving,
        main_route=main_route,
        timeline=[event],
        total_duration_hours=16.0
    )

    # Create Capacity
    capacity = Capacity(
        max_weight=24000.0,
        max_volume=80.0
    )

    # Create TransportType
    transport_type = TransportType(
        id=uuid4(),
        name="Standard Truck",
        capacity=capacity,
        restrictions=["ADR", "TEMP"]
    )

    # Create Cargo
    cargo = Cargo(
        id=uuid4(),
        type="General",
        weight=5000.0,
        value=50000.0,
        special_requirements=["Temperature Control"]
    )

    # Create CostSetting
    cost_item = CostSetting(
        id=uuid4(),
        type="fuel",
        category="variable",
        base_value=1.5,
        description="Fuel cost per km",
        multiplier=1.0,
        currency="EUR",
        is_enabled=True
    )

    # Create Offer
    offer = Offer(
        id=uuid4(),
        route_id=route.id,
        total_cost=1500.0,
        margin=0.15,
        final_price=1725.0,
        fun_fact="First commercial truck was built in 1896!",
        status="pending",
        created_at=datetime.now(),
        cost_breakdown={"fuel": 800.0, "driver": 500.0, "tolls": 200.0}
    )

    print("Successfully created all entity instances!")
    return True

if __name__ == "__main__":
    test_entity_creation()
