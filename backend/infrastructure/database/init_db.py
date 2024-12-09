from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.infrastructure.database.session import Base, SessionLocal, engine
from backend.infrastructure.database.models.cost_setting import CostSetting
from backend.infrastructure.database.models.route import RouteModel
from backend.infrastructure.database.models.offer import OfferModel
from backend.infrastructure.logging import logger

def init_db():
    """Initialize the database with required tables and initial data."""
    logger.info("initializing_database")
    
    try:
        # Create a new session
        session = SessionLocal()
        
        # Drop all existing tables
        logger.info("dropping_existing_tables")
        Base.metadata.drop_all(bind=engine)
        
        # Create new tables
        logger.info("creating_new_tables")
        Base.metadata.create_all(bind=engine)
        
        # Add initial cost settings if none exist
        initial_settings = [
            CostSetting(
                name="Base Distance Cost",
                type="distance",
                category="transport",
                value=2.0,
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Base cost per kilometer",
                created_by="system"
            ),
            CostSetting(
                name="Base Time Cost",
                type="time",
                category="transport",
                value=50.0,
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Base cost per hour",
                created_by="system"
            ),
            CostSetting(
                name="Base Loading Cost",
                type="loading",
                category="handling",
                value=25.0,
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Base cost for loading/unloading",
                created_by="system"
            )
        ]
        
        for setting in initial_settings:
            session.add(setting)
        session.commit()
        
        logger.info("database_initialized_successfully")
        
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
