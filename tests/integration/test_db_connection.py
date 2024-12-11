from backend.infrastructure.database.session import SessionLocal
from backend.infrastructure.database.models import Route, Offer
from datetime import datetime, timedelta, timezone
import uuid

def test_database_connection():
    # Create a new database session
    db = SessionLocal()
    try:
        # Create a test route
        route = Route(
            id=str(uuid.uuid4()),
            origin_address="Test Origin",
            origin_latitude=52.5200,
            origin_longitude=13.4050,
            destination_address="Test Destination",
            destination_latitude=51.5074,
            destination_longitude=-0.1278,
            pickup_time=datetime.now(timezone.utc),
            delivery_time=datetime.now(timezone.utc) + timedelta(days=1),
            total_duration_hours=24.0,
            is_feasible=True,
            duration_validation=True,
            transport_type={"type": "truck"},
            cargo={"weight": 1000},
            total_cost=1000.0,
            currency="EUR"
        )
        
        # Add and commit the route
        db.add(route)
        db.commit()
        db.refresh(route)
        print("✅ Successfully created route")

        # Create a test offer
        offer = Offer(
            route_id=route.id,
            cost_breakdown={"base_cost": 1000.0},
            margin_percentage=10.0,
            final_price=1100.0,
            currency="EUR",
            status="DRAFT",
            offer_metadata={}
        )
        
        # Add and commit the offer
        db.add(offer)
        db.commit()
        db.refresh(offer)
        print("✅ Successfully created offer")

        # Verify the relationship
        db_route = db.query(Route).filter(Route.id == route.id).first()
        print(f"✅ Route has {len(db_route.offers)} offers")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connection()
