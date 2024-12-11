import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.domain.entities import (
    Location, Route, EmptyDriving, MainRoute, CountrySegment,
    TimelineEvent, TransportType, Cargo, CostItem
)

@pytest.fixture
def mock_location():
    """Create a mock location for testing."""
    return Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )

@pytest.fixture
def mock_route(mock_location):
    """Create a mock route for testing."""
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
        timeline=[],
        total_duration_hours=16.0,
        is_feasible=True,
        duration_validation=True
    )

@pytest.fixture
def mock_cargo():
    """Create a mock cargo for testing."""
    return Cargo(
        id=uuid4(),
        type="General",
        weight=1000.0,
        value=5000.0,
        special_requirements=[]
    )

@pytest.fixture
def mock_transport_type():
    """Create a mock transport type for testing."""
    return TransportType(
        id=uuid4(),
        name="Standard Truck",
        capacity={"max_weight": 20000, "max_volume": 100},
        restrictions=[]
    )

@pytest.fixture
def mock_cost_items():
    """Create mock cost items for testing."""
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