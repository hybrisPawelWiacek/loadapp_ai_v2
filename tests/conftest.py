import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

from backend.domain.services import (
    RouteService,
    CostCalculationService,
    OfferService,
    CostOptimizationService
)
from backend.infrastructure.database.repositories.base_repository import BaseRepository
from backend.infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from backend.infrastructure.monitoring.metrics_service import MetricsService
from backend.domain.validators.cost_setting_validator import CostSettingValidator
from backend.infrastructure.database.repositories import (
    RouteRepository,
    OfferRepository
)

# Load test environment variables
load_dotenv(".env.development")

# Database configuration
TEST_DB_USER = os.getenv("DB_USER", "postgres")
TEST_DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
TEST_DB_HOST = os.getenv("DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("DB_PORT", "5432")
TEST_DB_NAME = "loadapp_test"

# Create test database URL
TEST_DATABASE_URL = f"postgresql+psycopg2://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

# Create Base for test models
Base = declarative_base()

@pytest.fixture(scope="session")
def test_engine():
    """Create test engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        isolation_level="AUTOCOMMIT",
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def TestSession(test_engine):
    """Create session factory."""
    return scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine
        )
    )

@pytest.fixture(scope="function")
def db_session(test_engine, TestSession):
    """Provide test database session with transaction rollback."""
    # Create a new connection
    connection = test_engine.connect()
    
    # Begin a non-ORM transaction
    transaction = connection.begin()
    
    # Bind the session to the connection
    session = TestSession(bind=connection)
    
    # Begin a nested transaction (using SAVEPOINT)
    session.begin_nested()
    
    # If the application code calls session.commit, it will only commit
    # up to the SAVEPOINT we created, rather than the actual database.
    # This allows us to roll back everything at the end of the test.
    
    @session.event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            # Begin a new nested transaction when the previous one commits
            session.begin_nested()
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()
    TestSession.remove()

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_engine):
    """Create test database and tables."""
    # Create a new connection to the default database
    default_db_url = f"postgresql+psycopg2://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres"
    default_engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
    
    with default_engine.connect() as conn:
        # Terminate all connections to the test database
        conn.execute(text(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid()
            """
        ))
        
        # Drop and recreate test database
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    
    # Import all models to ensure they are registered with Base
    from backend.infrastructure.database.models.route import RouteModel
    from backend.infrastructure.database.models.offer import OfferModel
    from backend.infrastructure.database.models.cost_setting import CostSettingModel
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    # Drop test database
    with default_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))

@pytest.fixture(scope="function", autouse=True)
def setup_test_data(db_session):
    """Initialize test data for each test."""
    # Create all tables
    Base.metadata.create_all(bind=db_session.get_bind())
    
    yield
    
    # Clean up tables after test
    Base.metadata.drop_all(bind=db_session.get_bind())

@pytest.fixture
def metrics_service():
    """Provide a metrics service instance."""
    return MetricsService()

@pytest.fixture
def base_repository(db_session):
    """Provide a base repository instance."""
    return BaseRepository(db_session, None)  # None as model_class will be set by child repos

@pytest.fixture
def route_repository(db_session):
    """Create a route repository instance."""
    return RouteRepository(db_session)

@pytest.fixture
def offer_repository(db_session):
    """Create an offer repository instance."""
    return OfferRepository(db_session)

@pytest.fixture
def cost_settings_repository(db_session):
    """Provide a cost settings repository instance."""
    repo = CostSettingsRepository(db_session)
    try:
        repo.initialize_default_settings()  # Initialize default settings for tests
    except Exception as e:
        db_session.rollback()  # Rollback on error
        raise
    return repo

@pytest.fixture
def cost_validator():
    """Create a cost validator instance."""
    return CostSettingValidator()

@pytest.fixture
def cost_optimization_service(metrics_service):
    """Create a cost optimization service instance."""
    return CostOptimizationService(metrics_service=metrics_service)

@pytest.fixture
def cost_calculation_service(
    cost_settings_repository,
    cost_optimization_service,
    metrics_service
):
    """Create a cost calculation service instance."""
    return CostCalculationService(
        cost_settings_repository=cost_settings_repository,
        cost_optimization_service=cost_optimization_service,
        metrics_service=metrics_service
    )

@pytest.fixture
def route_service(
    route_repository,
    cost_settings_repository,
    cost_calculation_service,
    cost_validator,
    metrics_service
):
    """Create a route service instance."""
    return RouteService(
        repository=route_repository,
        cost_settings_repository=cost_settings_repository,
        cost_calculation_service=cost_calculation_service,
        cost_validator=cost_validator,
        metrics_service=metrics_service
    )
