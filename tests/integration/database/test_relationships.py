import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from backend.infrastructure.database.models import Route, Offer, CostSetting
from sqlalchemy.exc import IntegrityError

class TestDatabaseRelationships:
    """Test database model relationships and constraints"""

    def test_route_offer_relationship(self, db_session):
        """Test one-to-many relationship between Route and Offers"""
        # Create route
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
        
        # Create multiple offers for the same route
        offers = [
            Offer(
                id=uuid4(),
                route_id=route.id,
                status="pending",
                base_price=1000.0 * (i + 1),
                margin_percentage=15.0,
                final_price=1150.0 * (i + 1),
                currency="EUR"
            )
            for i in range(3)
        ]
        
        db_session.bulk_save_objects(offers)
        db_session.commit()
        
        # Query route with offers
        queried_route = db_session.query(Route).filter_by(id=route.id).first()
        assert len(queried_route.offers) == 3
        assert all(offer.route_id == route.id for offer in queried_route.offers)

    def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraints"""
        # Try to create offer with non-existent route
        invalid_offer = Offer(
            id=uuid4(),
            route_id=uuid4(),  # Non-existent route_id
            status="pending",
            base_price=1000.0,
            margin_percentage=15.0,
            final_price=1150.0,
            currency="EUR"
        )
        
        with pytest.raises(IntegrityError):
            db_session.add(invalid_offer)
            db_session.commit()

    def test_cascade_operations(self, db_session):
        """Test cascade operations between related models"""
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
        
        offers = [
            Offer(
                id=uuid4(),
                route_id=route.id,
                status="pending",
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            )
            for _ in range(2)
        ]
        
        db_session.bulk_save_objects(offers)
        db_session.commit()
        
        # Delete route and verify cascade
        db_session.delete(route)
        db_session.commit()
        
        # Verify all related offers are deleted
        offer_count = db_session.query(Offer).filter_by(route_id=route.id).count()
        assert offer_count == 0

    def test_relationship_queries(self, db_session):
        """Test querying through relationships"""
        # Create route with multiple offers
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
        
        offers = [
            Offer(
                id=uuid4(),
                route_id=route.id,
                status=status,
                base_price=1000.0,
                margin_percentage=15.0,
                final_price=1150.0,
                currency="EUR"
            )
            for status in ["pending", "accepted", "rejected"]
        ]
        
        db_session.bulk_save_objects(offers)
        db_session.commit()
        
        # Query accepted offers for route
        accepted_offers = (
            db_session.query(Offer)
            .filter_by(route_id=route.id, status="accepted")
            .all()
        )
        assert len(accepted_offers) == 1
        
        # Query route through offer
        offer = accepted_offers[0]
        assert offer.route.origin_address == "Berlin, Germany"