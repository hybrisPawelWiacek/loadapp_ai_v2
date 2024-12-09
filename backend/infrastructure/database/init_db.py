from backend.infrastructure.database.db_setup import Base, engine, SessionLocal
from backend.infrastructure.database.models import Route, Offer, CostItem
import structlog
from datetime import datetime
from uuid import uuid4
from sqlalchemy import inspect

logger = structlog.get_logger(__name__)

def init_db():
    """Initialize the database with tables and default cost settings."""
    try:
        inspector = inspect(engine)
        
        # Drop existing tables if they exist
        if inspector.get_table_names():
            logger.info("dropping_existing_tables")
            Base.metadata.drop_all(bind=engine)
        
        # Create all tables with new schema
        logger.info("creating_new_tables")
        Base.metadata.create_all(bind=engine)
        
        # Create session
        session = SessionLocal()
        
        try:
            # Add default cost settings if they don't exist
            if session.query(CostItem).count() == 0:
                logger.info("adding_default_cost_settings")
                default_settings = [
                    CostItem(
                        id=uuid4(),
                        name="fuel_cost",
                        type="fuel",
                        category="variable",
                        value=1.5,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Fuel cost per kilometer"
                    ),
                    CostItem(
                        id=uuid4(),
                        name="driver_cost",
                        type="driver",
                        category="fixed",
                        value=25.0,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Driver hourly rate"
                    ),
                    CostItem(
                        id=uuid4(),
                        name="toll_cost",
                        type="toll",
                        category="variable",
                        value=0.2,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Average toll cost per kilometer"
                    ),
                    CostItem(
                        id=uuid4(),
                        name="maintenance_cost",
                        type="maintenance",
                        category="variable",
                        value=0.15,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Vehicle maintenance cost per kilometer"
                    ),
                    CostItem(
                        id=uuid4(),
                        name="insurance_cost",
                        type="insurance",
                        category="fixed",
                        value=50.0,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Daily insurance cost"
                    ),
                    CostItem(
                        id=uuid4(),
                        name="overhead_cost",
                        type="overhead",
                        category="fixed",
                        value=100.0,
                        multiplier=1.0,
                        currency="EUR",
                        is_enabled=True,
                        description="Daily overhead cost"
                    )
                ]
                
                session.add_all(default_settings)
                session.commit()
                logger.info("default_settings_added", count=len(default_settings))
                
        except Exception as e:
            session.rollback()
            logger.error("error_adding_default_settings", error=str(e))
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise
    else:
        logger.info("database_initialized_successfully")

if __name__ == "__main__":
    init_db()
