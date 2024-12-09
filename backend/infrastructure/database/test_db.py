from datetime import datetime, timedelta, timezone
from .db_setup import init_db, SessionLocal
from .repository import Repository
from backend.domain.entities import (
    Location, TransportType, Cargo, Route, MainRoute, EmptyDriving, CountrySegment,
    CostSetting, Offer
)
from uuid import uuid4

def test_database_setup():
    # Initialize the database
    init_db()
    
    # Create a database session
    db = SessionLocal()
    repo = Repository(db)
    
    try:
        # Create a test cost setting
        cost_setting = CostSetting(
            id=str(uuid4()),
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            description="Fuel cost per kilometer",
            is_enabled=True
        )
        db_cost_setting = repo.create_cost_setting(cost_setting.__dict__)
        print(f"Created cost setting: {db_cost_setting.id}")
        
        # Create test route with proper domain entities
        origin = Location(
            latitude=52.52,
            longitude=13.405,
            address="Berlin"
        )
        
        destination = Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris"
        )
        
        transport_type = TransportType(
            id=str(uuid4()),
            name="Standard Truck",
            capacity={"weight": 24000, "volume": 80},
            restrictions=["ADR", "TEMP_CONTROLLED"]
        )
        
        cargo = Cargo(
            id=str(uuid4()),
            type="general",
            weight=15000,
            value=50000,
            special_requirements=["TEMP_CONTROLLED"]
        )
        
        empty_driving = EmptyDriving(
            distance_km=200.0,
            duration_hours=4.0,
            country_segments=[CountrySegment(country="Germany", distance_km=200.0)],
            base_cost=100.0
        )
        
        main_route = MainRoute(
            distance_km=1050.0,
            duration_hours=12.0,
            country_segments=[
                CountrySegment(country="Germany", distance_km=500.0),
                CountrySegment(country="France", distance_km=550.0)
            ],
            base_cost=150.0
        )
        
        current_time = datetime.now(timezone.utc)
        route = Route(
            origin=origin,
            destination=destination,
            pickup_time=current_time,
            delivery_time=current_time + timedelta(days=1),
            transport_type=transport_type,
            cargo=cargo,
            empty_driving=empty_driving,
            main_route=main_route,
            timeline=[],
            total_duration_hours=16.0,
            is_feasible=True,
            duration_validation=True
        )
        
        db_route = repo.save_route(route)
        print(f"Created route: {db_route.id}")
        
        # Create a test offer
        offer = Offer(
            id=str(uuid4()),
            route_id=str(db_route.id),
            total_cost=1500.0,
            margin=0.15,
            final_price=1725.0,
            fun_fact="Did you know? The first commercial truck was built in 1896!",
            status="pending",
            created_at=datetime.now(timezone.utc),
            cost_breakdown={
                "fuel": 800.0,
                "driver": 500.0,
                "tolls": 200.0
            }
        )
        db_offer = repo.create_offer(offer.__dict__)
        print(f"Created offer: {db_offer.id}")
        
        # Test retrieving the data
        retrieved_cost_setting = repo.get_cost_setting(db_cost_setting.id)
        retrieved_route = repo.get_route(db_route.id)
        retrieved_offer = repo.get_offer(db_offer.id)

        print("\nTest Results:")
        print(f"Retrieved cost setting type: {retrieved_cost_setting.type}")
        print(f"Retrieved route origin latitude: {retrieved_route.origin.latitude}")
        print(f"Retrieved route destination: {retrieved_route.destination.address}")
        print(f"Retrieved offer total cost: {retrieved_offer.total_cost}")

        # Verify the data matches
        assert retrieved_cost_setting.type == "fuel"
        assert retrieved_route.origin.latitude == 52.52
        assert retrieved_route.destination.address == "Paris"
        assert retrieved_offer.total_cost == 1500.0

        print("\nAll tests passed successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_database_setup()
