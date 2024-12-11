import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool, NullPool

from backend.infrastructure.database.db_setup import Base

# Database configuration
SQLITE_URL = "sqlite:///:memory:"
POSTGRES_TEST_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/test_db'
)

def get_test_db_url(db_type: str = "sqlite") -> str:
    """Get database URL based on test type."""
    if db_type == "postgres":
        return POSTGRES_TEST_URL
    return SQLITE_URL

def create_sqlite_engine():
    """Create SQLite engine for fast tests."""
    return create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

def create_postgres_engine():
    """Create PostgreSQL engine for compatibility tests."""
    return create_engine(
        POSTGRES_TEST_URL,
        poolclass=NullPool,  # Disable connection pool for tests
        echo=False
    )

@pytest.fixture(scope="session")
def db_engine_sqlite():
    """Create a SQLite in-memory database engine for fast tests."""
    engine = create_sqlite_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def db_engine_postgres():
    """Create a PostgreSQL database engine for compatibility tests."""
    engine = create_postgres_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def db_session_factory_sqlite(db_engine_sqlite):
    """Create a factory for SQLite database sessions."""
    return sessionmaker(
        bind=db_engine_sqlite,
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

@pytest.fixture
def db_session_sqlite(db_session_factory_sqlite) -> Generator[Session, None, None]:
    """Create a new SQLite database session for fast tests."""
    session = db_session_factory_sqlite()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def db_session_postgres(db_session_factory_postgres) -> Generator[Session, None, None]:
    """Create a new PostgreSQL database session for compatibility tests."""
    session = db_session_factory_postgres()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def db_session(request) -> Generator[Session, None, None]:
    """Create a database session based on test type.
    
    Usage:
        @pytest.mark.db_type("postgres")
        def test_something(db_session):
            # Uses PostgreSQL

        def test_something_else(db_session):
            # Uses SQLite by default
    """
    db_type = getattr(request.node.get_closest_marker("db_type"), "args", ("sqlite",))[0]
    if db_type == "postgres":
        session = request.getfixturevalue("db_session_postgres")
    else:
        session = request.getfixturevalue("db_session_sqlite")
    return session

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "db_type(type): mark test to run with specific database type (sqlite/postgres)"
    ) 