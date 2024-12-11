import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.domain.services.route_service import RouteService
from backend.domain.entities import Location, Cargo, TransportType, Capacity

@pytest.mark.unit
class TestRoutePlanningService:
    """Test suite for route planning service."""

    @pytest.fixture
    def service(self):
        """Create route planning service instance."""
        return RouteService()

    @pytest.fixture
    def test_locations(self):
        """Create test locations for route planning."""
        return {
            "origin": Location(
                latitude=52.5200,
                longitude=13.4050,
                address="Berlin, Germany"
            ),
            "destination": Location(
                latitude=52.2297,
                longitude=21.0122,
                address="Warsaw, Poland"
            )
        }

    @pytest.fixture
    def test_transport_type(self):
        """Create test transport type."""
        return TransportType(
            id=uuid4(),
            name="TRUCK",
            capacity=Capacity(
                max_weight=24000,
                max_volume=80,
                unit="metric"
            ),
            restrictions=[]
        )

    @pytest.fixture
    def test_cargo(self):
        """Create test cargo."""
        return Cargo(
            id=uuid4(),
            type="general",
            weight=1000,
            value=5000.0,
            special_requirements=[]
        )

    def test_calculate_route_success(self, service, test_locations, test_transport_type, test_cargo):
        """Test successful route calculation with all parameters."""
        # Arrange
        pickup_time = datetime.now() + timedelta(days=1)
        delivery_time = pickup_time + timedelta(days=1)

        # Act
        route = service.calculate_route(
            origin=test_locations["origin"],
            destination=test_locations["destination"],
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            cargo=test_cargo,
            transport_type=test_transport_type
        )

        # Assert
        assert route is not None
        assert route.id is not None
        assert route.origin == test_locations["origin"]
        assert route.destination == test_locations["destination"]
        assert route.pickup_time == pickup_time
        assert route.delivery_time == delivery_time
        assert route.empty_driving is not None
        assert route.main_route is not None
        assert len(route.timeline) == 4  # start, pickup, rest, delivery
        assert route.total_duration_hours == route.empty_driving.duration_hours + route.main_route.duration_hours
        assert route.is_feasible is True

    def test_calculate_route_invalid_delivery_time(self, service, test_locations):
        """Test route calculation with invalid delivery time."""
        # Arrange
        pickup_time = datetime.now() + timedelta(days=1)
        delivery_time = pickup_time - timedelta(hours=1)  # Invalid: delivery before pickup

        # Act & Assert
        with pytest.raises(ValueError, match="Delivery time must be after pickup time"):
            service.calculate_route(
                origin=test_locations["origin"],
                destination=test_locations["destination"],
                pickup_time=pickup_time,
                delivery_time=delivery_time
            )

    def test_calculate_route_timeline_events(self, service, test_locations):
        """Test timeline events in calculated route."""
        # Arrange
        pickup_time = datetime.now() + timedelta(days=1)
        delivery_time = pickup_time + timedelta(days=1)

        # Act
        route = service.calculate_route(
            origin=test_locations["origin"],
            destination=test_locations["destination"],
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

    def test_route_validation(self, service, test_locations, test_transport_type, test_cargo):
        """Test route validation with various constraints."""
        # Arrange
        pickup_time = datetime.now() + timedelta(days=1)
        delivery_time = pickup_time + timedelta(hours=4)  # Too short duration

        # Act
        route = service.calculate_route(
            origin=test_locations["origin"],
            destination=test_locations["destination"],
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            cargo=test_cargo,
            transport_type=test_transport_type
        )

        # Assert
        assert route.is_feasible is False
        assert route.duration_validation is False

    def test_route_with_special_requirements(self, service, test_locations):
        """Test route calculation with special cargo requirements."""
        # Arrange
        special_cargo = Cargo(
            id=uuid4(),
            type="hazardous",
            weight=1000,
            value=10000.0,
            special_requirements=["ADR", "Temperature controlled"]
        )
        special_transport = TransportType(
            id=uuid4(),
            name="SPECIAL_TRUCK",
            capacity=Capacity(max_weight=24000, max_volume=80, unit="metric"),
            restrictions=["ADR", "Temperature controlled"]
        )
        pickup_time = datetime.now() + timedelta(days=1)
        delivery_time = pickup_time + timedelta(days=1)

        # Act
        route = service.calculate_route(
            origin=test_locations["origin"],
            destination=test_locations["destination"],
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            cargo=special_cargo,
            transport_type=special_transport
        )

        # Assert
        assert route.is_feasible is True
        assert any(event.event_type == "rest" for event in route.timeline)  # Special cargo requires rest stops
