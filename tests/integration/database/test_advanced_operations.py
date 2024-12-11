import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload
from backend.infrastructure.database.models import Route, Offer, CostSetting

class TestAdvancedDatabaseOperations:
    """Test advanced database operations and queries"""

    def test_complex_joins(self, db_session):
        """Test complex join operations"""
        # Create test data
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
        
        # Add offers with different statuses
        statuses = ["pending", "accepted", "rejected"]
        for status in statuses:
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                status=status,
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            )
            db_session.add(offer)
        
        db_session.commit()
        
        # Complex join query with aggregation
        results = (
            db_session.query(
                Route,
                func.count(Offer.id).label('offer_count'),
                func.avg(Offer.final_price).label('avg_price')
            )
            .join(Offer)
            .group_by(Route)
            .having(func.count(Offer.id) > 0)
            .first()
        )
        
        assert results.offer_count == 3
        assert results.avg_price == 1150.0

    def test_eager_loading(self, db_session):
        """Test eager loading of relationships"""
        # Create route with offers
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
        
        # Add multiple offers
        for _ in range(3):
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
        
        # Query with eager loading
        route_with_offers = (
            db_session.query(Route)
            .options(joinedload(Route.offers))
            .filter_by(id=route.id)
            .first()
        )
        
        assert len(route_with_offers.offers) == 3

    def test_transaction_rollback(self, db_session):
        """Test transaction rollback on error"""
        # Create initial route
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
        
        # Try to add valid and invalid offers in same transaction
        try:
            # Add valid offer
            valid_offer = Offer(
                id=uuid4(),
                route_id=route.id,
                status="pending",
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            )
            db_session.add(valid_offer)
            
            # Add invalid offer (missing required fields)
            invalid_offer = Offer(
                id=uuid4(),
                route_id=route.id  # Missing other required fields
            )
            db_session.add(invalid_offer)
            
            db_session.commit()
        except:
            db_session.rollback()
        
        # Verify transaction was rolled back
        offers = db_session.query(Offer).filter_by(route_id=route.id).all()
        assert len(offers) == 0

    def test_bulk_operations_with_constraints(self, db_session):
        """Test bulk operations with constraint checking"""
        # Create base route
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
        
        # Prepare mix of valid and invalid offers
        offers = [
            # Valid offer
            Offer(
                id=uuid4(),
                route_id=route.id,
                status="pending",
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            ),
            # Invalid offer (non-existent route)
            Offer(
                id=uuid4(),
                route_id=uuid4(),
                status="pending",
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            )
        ]
        
        # Attempt bulk save with error handling
        try:
            db_session.bulk_save_objects(offers)
            db_session.commit()
        except:
            db_session.rollback()
        
        # Verify only valid offers were saved
        saved_offers = db_session.query(Offer).filter_by(route_id=route.id).all()
        assert len(saved_offers) == 0  # All or nothing transaction 