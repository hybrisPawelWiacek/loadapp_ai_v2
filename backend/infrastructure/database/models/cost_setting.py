from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from datetime import datetime
from uuid import uuid4

from backend.infrastructure.database.session import Base

class CostSettingModel(Base):
    __tablename__ = "cost_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # Type of cost (e.g., fuel, maintenance)
    category = Column(String, nullable=False)  # Category for grouping
    value = Column(Float, nullable=False)  # Base cost value
    
    multiplier = Column(Float, nullable=False, default=1.0)
    currency = Column(String, nullable=False, default='EUR')
    is_enabled = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)
    
    # Additional metadata
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    validation_rules = Column(JSON, nullable=True)
    historical_data = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'value': self.value,
            'multiplier': self.multiplier,
            'currency': self.currency,
            'is_enabled': self.is_enabled,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'validation_rules': self.validation_rules,
            'historical_data': self.historical_data
        }

# Alias for backwards compatibility
CostSetting = CostSettingModel
