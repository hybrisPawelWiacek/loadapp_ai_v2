from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.session import Base, SQLALCHEMY_DATABASE_URL
from backend.infrastructure.database.models.cost_setting import CostSettingModel
from backend.infrastructure.database.models.route import RouteModel
from backend.infrastructure.database.models.offer import OfferModel, OfferVersionModel, OfferEventModel

def run_migrations():
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Add initial cost settings
        initial_settings = [
            CostSettingModel(
                name="Fuel Cost",
                type="fuel",
                category="variable",
                value=2.0,  # €2.0 per liter
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Cost per liter of fuel"
            ),
            CostSettingModel(
                name="Time Cost",
                type="time",
                category="variable",
                value=50.0,  # €50.0 per hour
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Cost per hour of driving"
            ),
            CostSettingModel(
                name="Maintenance Cost",
                type="maintenance",
                category="variable",
                value=0.5,  # €0.5 per km
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Vehicle maintenance cost per kilometer"
            ),
            CostSettingModel(
                name="Insurance Cost",
                type="insurance",
                category="base",
                value=100.0,  # €100.0 base insurance
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Base insurance cost per route"
            ),
            CostSettingModel(
                name="Weight-based Cost",
                type="weight",
                category="cargo-specific",
                value=0.1,  # €0.1 per kg
                multiplier=1.0,
                currency="EUR",
                is_enabled=True,
                description="Additional cost based on cargo weight"
            )
        ]
        
        # Add all settings
        for setting in initial_settings:
            db.add(setting)
        db.commit()
            
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migrations()
