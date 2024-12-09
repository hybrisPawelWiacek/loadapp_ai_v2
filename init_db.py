from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, CostSettings

# Create database engine
engine = create_engine('sqlite:///loadapp.db')

def init_db():
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if cost settings already exist
    existing_settings = session.query(CostSettings).first()
    
    if not existing_settings:
        # Create default cost settings
        default_settings = CostSettings(
            cost_per_token=0.0001,  # Default cost per token
            base_cost=0.01,         # Default base cost
            currency='USD'          # Default currency
        )
        
        # Add and commit the default settings
        session.add(default_settings)
        session.commit()
        print("Database initialized with default cost settings")
    else:
        print("Cost settings already exist in the database")
    
    session.close()

if __name__ == '__main__':
    init_db()
