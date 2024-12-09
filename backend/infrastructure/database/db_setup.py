from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Get the absolute path to the database file
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'loadapp.db'
DB_PATH.parent.mkdir(exist_ok=True)

# Create database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLAlchemy engine and Base
Base = declarative_base()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get a new database session."""
    return SessionLocal()

def init_db():
    """Initialize the database."""
    # Import models here to avoid circular imports
    from .models import Route, Offer, CostSetting, MetricLog, MetricAggregate, AlertRule, AlertEvent
    Base.metadata.create_all(bind=engine)
