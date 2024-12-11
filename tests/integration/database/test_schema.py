import pytest
from datetime import datetime, UTC
from backend.infrastructure.database.models import Route, Offer, CostSetting, MetricLog
from backend.infrastructure.database.config import DatabaseConfig
from uuid import uuid4

class TestDatabaseSchema:
    """Test database schema and model relationships"""

    def test_route_creation(self, test_db):
        """Test creating and querying a route"""
        route = Route(
            origin_latitude=52.52,
            origin_longitude=13.405,
            origin_address="Berlin",
            destination_latitude=48.8566,
            destination_longitude=2.3522,
            destination_address="Paris",
            pickup_time=datetime.now(UTC),
            delivery_time=datetime.now(UTC),
            total_duration_hours=8.5,
        )
        test_db.add(route)
        test_db.commit()
        
        assert route.id is not None
        assert route.created_at.tzinfo is not None  # Verify timezone-aware

    def test_offer_creation(self, db_session):
        """Test creating and querying an offer with route relationship"""
        # Create route first
        route = Route(
            id=uuid4(),
            origin_address="Berlin, Germany",
            origin_lat=52.5200,
            origin_lon=13.4050,
            destination_address="Paris, France",
            destination_lat=48.8566,
            destination_lon=2.3522,
            pickup_time=datetime.now(),
            delivery_time=datetime.now() + timedelta(days=1),
            distance_km=1000.0,
            duration_hours=12.0,
            is_feasible=True
        )
        
        db_session.add(route)
        db_session.commit()
        
        # Create offer linked to route
        offer = Offer(
            id=uuid4(),
            route_id=route.id,
            status="pending",
            base_price=1000.0,
            margin_percentage=15.0,
            final_price=1150.0,
            currency="EUR"
        )
        
        db_session.add(offer)
        db_session.commit()
        
        # Query offer with route
        queried_offer = db_session.query(Offer).filter_by(id=offer.id).first()
        assert queried_offer is not None
        assert queried_offer.route_id == route.id
        assert queried_offer.route.origin_address == "Berlin, Germany"

    def test_cost_items(self, db_session):
        """Test cost items creation and relationships"""
        cost_item = CostSetting(
            id=uuid4(),
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Fuel cost per kilometer"
        )
        
        db_session.add(cost_item)
        db_session.commit()
        
        # Query cost item
        queried_item = db_session.query(CostSetting).filter_by(id=cost_item.id).first()
        assert queried_item is not None
        assert queried_item.type == "fuel"
        assert queried_item.base_value == 1.5

    def test_database_constraints(self, db_session):
        """Test database constraints and validations"""
        # Test unique constraint
        route_id = uuid4()
        
        # Create first offer
        offer1 = Offer(
            id=uuid4(),
            route_id=route_id,
            status="pending",
            base_price=1000.0,
            margin_percentage=15.0,
            final_price=1150.0,
            currency="EUR"
        )
        
        db_session.add(offer1)
        db_session.commit()
        
        # Try to create another offer with same ID
        offer2 = Offer(
            id=offer1.id,  # Same ID should violate unique constraint
            route_id=route_id,
            status="pending",
            base_price=2000.0,
            margin_percentage=15.0,
            final_price=2300.0,
            currency="EUR"
        )
        
        with pytest.raises(Exception):  # Should raise unique constraint violation
            db_session.add(offer2)
            db_session.commit()

    def test_cascade_delete(self, db_session):
        """Test cascade delete behavior"""
        # Create route and offer
        route = Route(
            id=uuid4(),
            origin_address="Berlin, Germany",
            origin_lat=52.5200,
            origin_lon=13.4050,
            destination_address="Paris, France",
            destination_lat=48.8566,
            destination_lon=2.3522,
            pickup_time=datetime.now(),
            delivery_time=datetime.now() + timedelta(days=1),
            distance_km=1000.0,
            duration_hours=12.0,
            is_feasible=True
        )
        
        db_session.add(route)
        db_session.commit()
        
        offer = Offer(
            id=uuid4(),
            route_id=route.id,
            status="pending",
            base_price=1000.0,
            margin_percentage=15.0,
            final_price=1150.0,
            currency="EUR"
        )
        
        db_session.add(offer)
        db_session.commit()
        
        # Delete route should cascade to offer
        db_session.delete(route)
        db_session.commit()
        
        # Verify offer is also deleted
        deleted_offer = db_session.query(Offer).filter_by(id=offer.id).first()
        assert deleted_offer is None 

    def test_offer_timestamps(self, db_session):
        """Test offer timestamps creation and relationships"""
        offer = Offer(
            route_id=uuid4(),
            final_price=100.0,
            currency='EUR',
            status='DRAFT',
            cost_breakdown={},
            margin_percentage=10.0
        )
        db_session.add(offer)
        db_session.commit()
        
        assert offer.created_at.tzinfo is not None
        assert offer.updated_at.tzinfo is not None 