from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from backend.infrastructure.database.session import Base

class RouteModel(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Location fields
    origin_address = Column(String, nullable=False)
    origin_latitude = Column(Float, nullable=False)
    origin_longitude = Column(Float, nullable=False)
    destination_address = Column(String, nullable=False)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    
    # Time fields
    pickup_time = Column(DateTime, nullable=False)
    delivery_time = Column(DateTime, nullable=False)
    last_calculated = Column(DateTime)
    
    # Route details
    total_duration_hours = Column(Float)
    total_cost = Column(Float)
    currency = Column(String, default="EUR")
    is_feasible = Column(Boolean, default=True)
    duration_validation = Column(Boolean, default=True)
    
    # JSON fields for complex types
    empty_driving = Column(JSON)
    main_route = Column(JSON)
    timeline = Column(JSON)
    timeline_events = Column(JSON)
    transport_type = Column(JSON)
    cargo = Column(JSON)
    cost_breakdown = Column(JSON)
    optimization_insights = Column(JSON)
    
    # Relationships
    offers = relationship("OfferModel", back_populates="route")

    def to_dict(self):
        """Convert route model to dictionary."""
        return {
            'id': str(self.id) if self.id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'origin': {
                'address': self.origin_address,
                'latitude': self.origin_latitude,
                'longitude': self.origin_longitude
            },
            'destination': {
                'address': self.destination_address,
                'latitude': self.destination_latitude,
                'longitude': self.destination_longitude
            },
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'total_duration_hours': self.total_duration_hours,
            'total_cost': self.total_cost,
            'currency': self.currency,
            'is_feasible': self.is_feasible,
            'duration_validation': self.duration_validation,
            'empty_driving': self.empty_driving,
            'main_route': self.main_route,
            'timeline': self.timeline,
            'timeline_events': self.timeline_events,
            'transport_type': self.transport_type,
            'cargo': self.cargo,
            'cost_breakdown': self.cost_breakdown,
            'optimization_insights': self.optimization_insights
        }

# Alias for backwards compatibility
Route = RouteModel
