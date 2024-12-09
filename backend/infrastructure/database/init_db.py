from backend.infrastructure.database.db_setup import Base, engine, SessionLocal
from backend.infrastructure.database.models import Route, Offer, CostSetting

def init_db():
    """Initialize the database with tables and default cost settings."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session using shared SessionLocal
    session = SessionLocal()
    
    try:
        # Add default cost settings if they don't exist
        if session.query(CostSetting).count() == 0:
            default_settings = [
                CostSetting(
                    type="fuel",
                    category="variable",
                    base_value=1.5,  # EUR per km
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Fuel cost per kilometer"
                ),
                CostSetting(
                    type="driver",
                    category="variable",
                    base_value=30.0,  # EUR per hour
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Driver cost per hour"
                ),
                CostSetting(
                    type="toll",
                    category="variable",
                    base_value=0.2,  # EUR per km
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Average toll cost per kilometer"
                ),
                CostSetting(
                    type="maintenance",
                    category="variable",
                    base_value=0.1,  # EUR per km
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Vehicle maintenance cost per kilometer"
                ),
                CostSetting(
                    type="insurance",
                    category="fixed",
                    base_value=100.0,  # EUR per day
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Daily insurance cost"
                ),
                CostSetting(
                    type="overhead",
                    category="fixed",
                    base_value=200.0,  # EUR per day
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Daily overhead costs"
                )
            ]
            
            session.add_all(default_settings)
            session.commit()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
