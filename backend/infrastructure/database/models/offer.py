from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..session import Base
from .base_version import BaseVersionModel
from ....domain.entities.offer import OfferStatus, Currency

class OfferModel(Base):
    """SQLAlchemy model for offers."""
    __tablename__ = 'offers'

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Cost and pricing
    cost_breakdown = Column(JSON, nullable=False, default=dict)
    margin_percentage = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False)
    
    # Status and tracking
    status = Column(SQLEnum(OfferStatus), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Additional data
    offer_metadata = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    route = relationship("RouteModel", back_populates="offers")
    versions = relationship("OfferVersionModel", back_populates="offer", cascade="all, delete-orphan")
    events = relationship("OfferEventModel", back_populates="offer", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'route_id': str(self.route_id) if self.route_id else None,
            'client_id': str(self.client_id) if self.client_id else None,
            'cost_breakdown': self.cost_breakdown,
            'margin_percentage': self.margin_percentage,
            'final_price': self.final_price,
            'currency': self.currency.value if self.currency else None,
            'status': self.status.value if self.status else None,
            'version': self.version,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.offer_metadata
        }

class OfferVersionModel(BaseVersionModel):
    """SQLAlchemy model for offer versions."""
    __tablename__ = 'offer_versions'

    # Override entity_id with offer-specific foreign key
    entity_id = Column(UUID(as_uuid=True), ForeignKey('offers.id'), nullable=False)
    
    # Relationships
    offer = relationship("OfferModel", back_populates="versions")

class OfferEventModel(Base):
    """SQLAlchemy model for offer events."""
    __tablename__ = 'offer_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('offers.id'), nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    event_metadata = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    offer = relationship("OfferModel", back_populates="events")

# Alias OfferModel as Offer for backwards compatibility
Offer = OfferModel
