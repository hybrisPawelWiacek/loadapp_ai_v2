from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a 'data' directory if it doesn't exist
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# SQLite database file path
DATABASE_FILE = os.path.join(DATA_DIR, 'windsurf.db')

# Database URL for SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create engine with SQLite-specific configurations
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=True  # Set to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    Base.metadata.create_all(bind=engine)
