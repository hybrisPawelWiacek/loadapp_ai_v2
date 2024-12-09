from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class CostSettings(Base):
    __tablename__ = 'cost_settings'
    
    id = Column(Integer, primary_key=True)
    cost_per_token = Column(Float, nullable=False)
    base_cost = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LoadTest(Base):
    __tablename__ = 'load_tests'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = relationship("LoadTestResult", back_populates="load_test")

class LoadTestResult(Base):
    __tablename__ = 'load_test_results'
    
    id = Column(Integer, primary_key=True)
    load_test_id = Column(Integer, ForeignKey('load_tests.id'))
    response_time = Column(Float)
    status_code = Column(Integer)
    error_message = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    load_test = relationship("LoadTest", back_populates="results")
