import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from backend.infrastructure.database.db_setup import engine, Base
from backend.infrastructure.database.models import Route, Offer, CostSetting, MetricLog, MetricAggregate, AlertRule, AlertEvent

def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!")
