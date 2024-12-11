import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from backend.domain.entities.route import Route, MainRoute, EmptyDriving, CountrySegment
from backend.domain.entities.location import Location
from backend.domain.entities.timeline import TimelineEvent
from backend.domain.entities.cargo import Cargo, TransportType

class TestRouteEntity:
    def test_route_creation(self, mock_location):
        """Test creating a valid route"""
        route = Route(
            id=uuid4(),
            origin=mock_location,
            destination=Location(
                latitude=48.8566,
                longitude=2.3522,
                address="Paris, France"
            ),
            pickup_time=datetime.now(),
            delivery_time=datetime.now() + timedelta(days=1),
            empty_driving=EmptyDriving(),
            main_route=MainRoute(
                distance_km=1000.0,
                duration_hours=12.0,
                country_segments=[
                    CountrySegment(
                        country="Germany",
                        distance_km=400.0,
                        duration_hours=5.0
                    ),
                    CountrySegment(
                        country="France",
                        distance_km=600.0,
                        duration_hours=7.0
                    )
                ]
            ),
            timeline=[],
            transport_type=None,
            cargo=None,
            is_feasible=True,
            total_cost=0.0,
            currency="EUR",
            cost_breakdown={},
            optimization_insights={}
        )
        
        assert route.origin.address == "Berlin, Germany"
        assert route.main_route.distance_km == 1000.0
        assert len(route.main_route.country_segments) == 2

    def test_route_validation(self):
        """Test route validation rules"""
        with pytest.raises(ValueError):
            Route(
                id=uuid4(),
                origin=None,  # Invalid: missing origin
                destination=None,  # Invalid: missing destination
                pickup_time=None,
                delivery_time=None,
                empty_driving=EmptyDriving(),
                main_route=None,
                timeline=[],
                transport_type=None,
                cargo=None,
                is_feasible=False,
                total_cost=0.0,
                currency="EUR",
                cost_breakdown={},
                optimization_insights={}
            )

    def test_route_creation_with_timezone(self):
        pickup_time = datetime.now(UTC)
        delivery_time = datetime.now(UTC)
        
        route = Route(
            pickup_time=pickup_time,
            delivery_time=delivery_time
        )
        
        assert route.pickup_time.tzinfo is not None
        assert route.delivery_time.tzinfo is not None

class TestTimelineEntity:
    def test_timeline_event_creation(self, mock_location):
        """Test creating timeline events"""
        event = TimelineEvent(
            event_type="start",
            location=mock_location,
            planned_time=datetime.now(),
            duration_minutes=30,
            description="Loading at origin",
            is_required=True
        )
        
        assert event.event_type == "start"
        assert event.duration_minutes == 30
        assert event.is_required is True

    def test_timeline_validation(self):
        """Test timeline event validation"""
        with pytest.raises(ValueError):
            TimelineEvent(
                event_type="invalid_type",
                location=None,
                planned_time=None,
                duration_minutes=-1,
                description="",
                is_required=None
            )

class TestLocationEntity:
    def test_location_creation(self):
        """Test creating location"""
        location = Location(
            latitude=52.5200,
            longitude=13.4050,
            address="Berlin, Germany"
        )
        
        assert location.latitude == 52.5200
        assert location.longitude == 13.4050
        assert location.address == "Berlin, Germany"

    def test_location_validation(self):
        """Test location validation rules"""
        with pytest.raises(ValueError):
            Location(
                latitude=1000.0,  # Invalid latitude
                longitude=2000.0,  # Invalid longitude
                address=""  # Empty address
            )

class TestCargoEntity:
    def test_cargo_creation(self):
        """Test creating cargo"""
        cargo = Cargo(
            type="General",
            weight=1000.0,
            value=5000.0,
            special_requirements=[]
        )
        
        assert cargo.type == "General"
        assert cargo.weight == 1000.0
        assert cargo.value == 5000.0

    def test_cargo_validation(self):
        """Test cargo validation rules"""
        with pytest.raises(ValueError):
            Cargo(
                type="Invalid",
                weight=-1.0,  # Invalid weight
                value=-100.0,  # Invalid value
                special_requirements=None
            )

class TestOfferEntity:
    def test_offer_expiration(self):
        current_time = datetime.now(UTC)
        expiration_time = current_time.replace(hour=current_time.hour + 1)
        
        offer = Offer(
            expires_at=expiration_time
        )
        
        assert not offer.is_expired(current_time)
