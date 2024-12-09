import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.db_setup import Base
from backend.infrastructure.database.models import Route, Offer, CostSetting

def init_db():
    db_path = os.path.join(project_root, 'loadapp.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.drop_all(engine)  # Drop all tables first
    Base.metadata.create_all(engine)  # Create tables with new schema
    print(f"Database recreated at {db_path}")

if __name__ == "__main__":
    init_db()
