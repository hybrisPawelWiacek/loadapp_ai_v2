import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.domain.entities import (
    Location, Route, EmptyDriving, MainRoute, CountrySegment,
    TimelineEvent, TransportType, Cargo, CostItem
)
from backend.infrastructure.database.repository import Repository

@pytest.fixture
def mock_location():
    return Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )

@pytest.fixture
def mock_route(mock_location):
    return Route(
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
            ),
            TimelineEvent(
                event_type="end",
                location=mock_location,
                planned_time=datetime.now() + timedelta(days=1),
                duration_minutes=0,
                description="End of route",
                is_required=True
            )
        ],
        total_duration_hours=16.0,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def mock_transport_type():
    return TransportType(
        id=uuid4(),
        name="Standard Truck",
        capacity={"max_weight": 20000, "max_volume": 100},
        restrictions=[]
    )

@pytest.fixture
def mock_cargo():
    return Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,
        value=5000.0,
        special_requirements=[]
    )

@pytest.fixture
def mock_cost_items():
    return [
        CostItem(
            id=uuid4(),
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Fuel cost per kilometer"
        ),
        CostItem(
            id=uuid4(),
            type="driver",
            category="variable",
            base_value=30.0,
            multiplier=1.0,
            currency="EUR",
            is_enabled=True,
            description="Driver wages per hour"
        )
    ]

@pytest.fixture
def mock_ai_service():
    class MockAIIntegrationService:
        def generate_transport_fun_fact(self, origin, destination, distance_km):
            return "This is a mock fun fact for testing purposes."
    return MockAIIntegrationService()

@pytest.fixture
def mock_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.infrastructure.database.db_setup import Base
    
    # Use an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for testing
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield Repository(db)
    finally:
        db.close()
