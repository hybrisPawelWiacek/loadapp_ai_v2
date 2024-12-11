import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from backend.infrastructure.database.models import Route, Offer, CostSetting
from sqlalchemy.exc import IntegrityError

class TestDatabaseCRUD:
    """Test basic CRUD operations for database models"""

    def test_route_crud(self, db_session):
        """Test Create, Read, Update, Delete operations for Route"""
        # Create
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
        
        # Read
        queried_route = db_session.query(Route).filter_by(id=route.id).first()
        assert queried_route is not None
        assert queried_route.origin_address == "Berlin, Germany"
        
        # Update
        queried_route.distance_km = 1100.0
        db_session.commit()
        
        updated_route = db_session.query(Route).filter_by(id=route.id).first()
        assert updated_route.distance_km == 1100.0
        
        # Delete
        db_session.delete(queried_route)
        db_session.commit()
        
        deleted_route = db_session.query(Route).filter_by(id=route.id).first()
        assert deleted_route is None

    def test_offer_crud(self, db_session):
        """Test CRUD operations for Offer with route relationship"""
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
        
        # Create offer
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
        
        # Read with relationship
        queried_offer = db_session.query(Offer).filter_by(id=offer.id).first()
        assert queried_offer is not None
        assert queried_offer.route.origin_address == "Berlin, Germany"
        
        # Update
        queried_offer.status = "accepted"
        queried_offer.margin_percentage = 20.0
        db_session.commit()
        
        updated_offer = db_session.query(Offer).filter_by(id=offer.id).first()
        assert updated_offer.status == "accepted"
        assert updated_offer.margin_percentage == 20.0
        
        # Delete
        db_session.delete(queried_offer)
        db_session.commit()
        
        deleted_offer = db_session.query(Offer).filter_by(id=offer.id).first()
        assert deleted_offer is None

    def test_cost_item_crud(self, db_session):
        """Test CRUD operations for CostItem"""
        # Create
        cost_item = CostSetting(
            id=uuid4(),
            name="Fuel Cost",
            type="fuel",
            category="variable",
            value=1.5,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Fuel cost per kilometer"
        )
        
        db_session.add(cost_item)
        db_session.commit()
        
        # Read
        queried_item = db_session.query(CostSetting).filter_by(id=cost_item.id).first()
        assert queried_item is not None
        assert queried_item.type == "fuel"
        
        # Update
        queried_item.value = 2.0
        queried_item.multiplier = 1.2
        db_session.commit()
        
        updated_item = db_session.query(CostSetting).filter_by(id=cost_item.id).first()
        assert updated_item.value == 2.0
        assert updated_item.multiplier == 1.2
        
        # Delete
        db_session.delete(queried_item)
        db_session.commit()
        
        deleted_item = db_session.query(CostSetting).filter_by(id=cost_item.id).first()
        assert deleted_item is None

    def test_bulk_operations(self, db_session):
        """Test bulk create and update operations"""
        # Bulk create routes
        routes = [
            Route(
                id=uuid4(),
                origin_address=f"City {i}",
                origin_lat=50.0 + i,
                origin_lon=10.0 + i,
                destination_address=f"Destination {i}",
                destination_lat=51.0 + i,
                destination_lon=11.0 + i,
                pickup_time=datetime.now(),
                delivery_time=datetime.now() + timedelta(days=1),
                distance_km=1000.0 + i,
                duration_hours=12.0,
                is_feasible=True
            )
            for i in range(3)
        ]
        
        db_session.bulk_save_objects(routes)
        db_session.commit()
        
        # Verify bulk create
        route_count = db_session.query(Route).count()
        assert route_count == 3
        
        # Bulk update
        db_session.query(Route).update({"is_feasible": False})
        db_session.commit()
        
        # Verify bulk update
        infeasible_count = db_session.query(Route).filter_by(is_feasible=False).count()
        assert infeasible_count == 3