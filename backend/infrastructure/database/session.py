from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError
import os
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv("DB_USER", "pawelwiacek")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "loadapp")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # Recycle connections after 30 minutes

def create_engine_with_retries(retries=3, delay=1):
    """Create database engine with retry logic for initial connection."""
    for attempt in range(retries):
        try:
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_timeout=POOL_TIMEOUT,
                pool_recycle=POOL_RECYCLE,
                pool_pre_ping=True,  # Enable connection health checks
            )
            return engine
        except OperationalError as e:
            if attempt == retries - 1:
                raise
            logger.warning(f"Database connection attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

engine = create_engine_with_retries()

# Configure connection pool event listeners
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.debug("New database connection established")

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection checked out from pool")

@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.debug("Database connection returned to pool")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Get a database session with automatic cleanup."""
    db = SessionLocal()
    try:
        # Test the connection before yielding
        db.execute("SELECT 1")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()
