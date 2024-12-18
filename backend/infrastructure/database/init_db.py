import logging
from sqlalchemy import inspect, text
from .session import Base, engine, SessionLocal
from ..database.models.cost_setting import CostSetting

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database."""
    logger.info("initializing_database")
    
    inspector = inspect(engine)
    session = SessionLocal()
    
    try:
        # For SQLite, we'll drop all tables safely
        if engine.url.drivername == 'sqlite':
            # Disable foreign key checks temporarily
            session.execute(text('PRAGMA foreign_keys=OFF'))
            session.commit()
            
            # Drop all tables
            Base.metadata.drop_all(bind=engine)
            
            # Re-enable foreign key checks
            session.execute(text('PRAGMA foreign_keys=ON'))
            session.commit()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add initial cost settings if none exist
        if not session.query(CostSetting).first():
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
        logger.error(f"database_initialization_failed error={str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
