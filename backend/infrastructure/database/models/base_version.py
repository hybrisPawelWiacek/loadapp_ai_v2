from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..session import Base

class BaseVersionModel(Base):
    """Base SQLAlchemy model for entity versions."""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    change_reason = Column(String, nullable=True)
    version_metadata = Column(JSON, nullable=False, default=dict)

    def to_dict(self):
        """Convert version model to dictionary."""
        return {
            'id': str(self.id),
            'entity_id': str(self.entity_id),
            'version': self.version,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'change_reason': self.change_reason,
            'version_metadata': self.version_metadata
        }
