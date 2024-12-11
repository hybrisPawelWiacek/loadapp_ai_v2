import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from backend.domain.services.offer_service import OfferService
from backend.domain.entities.route import Route, MainRoute, EmptyDriving, CountrySegment
from backend.domain.entities.location import Location
from backend.domain.entities.timeline import TimelineEvent
from backend.domain.entities.cargo import Cargo, TransportType

class TestOfferFilters:
    @pytest.fixture
    def filter_service(self):
        """Initialize offer filter service"""
        return OfferService()

    @pytest.fixture
    def sample_offers(self, mock_location):
        """Create sample offers for testing"""
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
            timeline=[
                TimelineEvent(
                    event_type="start",
                    location=mock_location,
                    planned_time=datetime.now(),
                    duration_minutes=0,
                    description="Start of route",
                    is_required=True
                )
            ],
            transport_type=None,
            cargo=None,
            is_feasible=True,
            total_cost=1000.0,
            currency="EUR",
            cost_breakdown={},
            optimization_insights={}
        )

        return [
            {
                "id": str(uuid4()),
                "route_id": str(route.id),
                "status": "pending",
                "base_price": 1000.0,
                "margin_percentage": 15.0,
                "final_price": 1150.0,
                "currency": "EUR",
                "route": route
            },
            {
                "id": str(uuid4()),
                "route_id": str(route.id),
                "status": "accepted",
                "base_price": 1200.0,
                "margin_percentage": 20.0,
                "final_price": 1440.0,
                "currency": "EUR",
                "route": route
            }
        ]

    def test_filter_by_status(self, filter_service, sample_offers):
        """Test filtering offers by status"""
        filtered = filter_service.filter_by_status(sample_offers, "pending")
        assert len(filtered) == 1
        assert filtered[0]["status"] == "pending"

    def test_filter_by_price_range(self, filter_service, sample_offers):
        """Test filtering offers by price range"""
        filtered = filter_service.filter_by_price_range(
            sample_offers,
            min_price=1200.0,
            max_price=1500.0
        )
        assert len(filtered) == 1
        assert filtered[0]["final_price"] == 1440.0

    def test_filter_by_date_range(self, filter_service, sample_offers):
        """Test filtering offers by date range"""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=2)
        
        filtered = filter_service.filter_by_date_range(
            sample_offers,
            start_date=start_date,
            end_date=end_date
        )
        assert len(filtered) == 2

    def test_filter_by_location(self, filter_service, sample_offers):
        """Test filtering offers by location"""
        filtered = filter_service.filter_by_location(
            sample_offers,
            country="Germany"
        )
        assert len(filtered) == 2  # Both offers have route through Germany

    def test_combined_filters(self, filter_service, sample_offers):
        """Test applying multiple filters"""
        filters = {
            "status": "pending",
            "min_price": 1000.0,
            "max_price": 1200.0,
            "country": "Germany"
        }
        
        filtered = filter_service.apply_filters(sample_offers, filters)
        assert len(filtered) == 1
        assert filtered[0]["status"] == "pending"
        assert 1000.0 <= filtered[0]["final_price"] <= 1200.0

    def test_offer_filter_by_date(self):
        test_date = datetime.now(UTC)
        filter = OfferFilter()
        
        offer = {
            'created_at': test_date,
            'expires_at': test_date
        }
        
        assert filter.is_valid(offer) == True
