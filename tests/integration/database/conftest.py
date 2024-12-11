import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    from backend.flask_app import db
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session()
    yield session
    session.close()
    transaction.rollback()
    connection.close() 