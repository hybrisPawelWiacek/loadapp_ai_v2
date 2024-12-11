import pytest
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.infrastructure.database.db_setup import Base
from backend.infrastructure.database.models import Route, Offer
from backend.domain.entities import Location, Route as RouteEntity

# Performance-optimized database setup
@pytest.fixture(scope="session")
def db_engine():
    """Create a SQLite in-memory database engine for the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # Increase SQLite timeout for better concurrency
        },
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def db_engine_postgres():
    """Create a PostgreSQL database engine for performance testing."""
    engine = create_engine(
        "postgresql+psycopg://postgres@localhost:5432/loadapp_test",
        connect_args={
            "application_name": "loadapp_perf_test",
            "sslmode": "prefer",
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 10,
            "keepalives_count": 3
        },
        pool_size=10,  # Increased pool size for performance tests
        max_overflow=20,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Create a factory for database sessions."""
    return sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False
    )

@pytest.fixture(scope="session")
def db_session_factory_postgres(db_engine_postgres):
    """Create a factory for PostgreSQL database sessions."""
    return sessionmaker(
        bind=db_engine_postgres,
        expire_on_commit=False,
        autoflush=False
    )

@pytest.fixture(scope="function")
def db_session(db_session_factory) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    session = db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def db_session_postgres(db_session_factory_postgres) -> Generator[Session, None, None]:
    """Create a new PostgreSQL database session for performance testing."""
    session = db_session_factory_postgres()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

# Cached test data
@pytest.fixture(scope="session")
def cached_locations() -> Dict[str, Location]:
    """Create a cache of commonly used locations."""
    return {
        "berlin": Location(
            latitude=52.5200,
            longitude=13.4050,
            address="Berlin, Germany"
        ),
        "paris": Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        "munich": Location(
            latitude=48.1351,
            longitude=11.5820,
            address="Munich, Germany"
        )
    }

@pytest.fixture(scope="session")
def cached_route_data(cached_locations) -> Dict[str, Any]:
    """Create cached route data for performance-critical tests."""
    return {
        "standard": {
            "origin": cached_locations["berlin"],
            "destination": cached_locations["paris"],
            "transport_type": {
                "type": "truck",
                "capacity": {"max_weight": 24000, "max_volume": 80}
            },
            "cargo": {
                "weight": 15000,
                "type": "general",
                "value": 50000
            }
        },
        "express": {
            "origin": cached_locations["munich"],
            "destination": cached_locations["paris"],
            "transport_type": {
                "type": "express",
                "capacity": {"max_weight": 12000, "max_volume": 40}
            },
            "cargo": {
                "weight": 8000,
                "type": "express",
                "value": 80000
            }
        }
    }

# Bulk data creation helpers
def create_bulk_routes(session: Session, count: int) -> list[Route]:
    """Create multiple routes efficiently."""
    routes = []
    for i in range(count):
        route = Route(
            origin_latitude=52.5200,
            origin_longitude=13.4050,
            origin_address=f"Origin {i}",
            destination_latitude=48.8566,
            destination_longitude=2.3522,
            destination_address=f"Destination {i}",
            total_cost=1000.0 + i
        )
        routes.append(route)
    session.bulk_save_objects(routes)
    session.commit()
    return routes

def create_bulk_offers(session: Session, route_ids: list[str], count_per_route: int) -> list[Offer]:
    """Create multiple offers efficiently."""
    offers = []
    for route_id in route_ids:
        for i in range(count_per_route):
            offer = Offer(
                route_id=route_id,
                total_cost=1000.0 + (i * 100),
                margin=0.15 + (i * 0.01),
                final_price=1200.0 + (i * 100),
                status="pending"
            )
            offers.append(offer)
    session.bulk_save_objects(offers)
    session.commit()
    return offers

# Performance test fixtures
@pytest.fixture(scope="function")
def performance_dataset(db_session):
    """Create a large dataset for performance testing."""
    routes = create_bulk_routes(db_session, 100)
    route_ids = [route.id for route in routes]
    offers = create_bulk_offers(db_session, route_ids, 5)
    return {
        "routes": routes,
        "offers": offers
    }

@pytest.fixture(scope="function")
def cleanup_performance_data(db_session):
    """Clean up performance test data after test."""
    yield
    db_session.query(Offer).delete()
    db_session.query(Route).delete()
    db_session.commit()

# Query optimization helpers
def optimize_query_for_route_listing(session: Session, filters: Dict[str, Any]) -> list[RouteEntity]:
    """Optimize route listing query for performance."""
    query = session.query(Route)
    
    # Add specific joins only if needed
    if filters.get("with_offers"):
        query = query.join(Offer)
    
    # Add specific columns only if needed
    if filters.get("minimal"):
        query = query.with_entities(
            Route.id,
            Route.origin_address,
            Route.destination_address,
            Route.total_cost
        )
    
    # Add specific filters
    if filters.get("min_cost"):
        query = query.filter(Route.total_cost >= filters["min_cost"])
    if filters.get("max_cost"):
        query = query.filter(Route.total_cost <= filters["max_cost"])
    
    # Optimize ordering
    if filters.get("order_by"):
        query = query.order_by(filters["order_by"])
    
    # Add pagination
    if filters.get("limit"):
        query = query.limit(filters["limit"])
    if filters.get("offset"):
        query = query.offset(filters["offset"])
    
    return query.all() 