from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .db_setup import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_latitude = Column(Float, nullable=False)
    origin_longitude = Column(Float, nullable=False)
    origin_address = Column(String, nullable=False)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    destination_address = Column(String, nullable=False)
    pickup_time = Column(DateTime, nullable=False)
    delivery_time = Column(DateTime, nullable=False)
    total_duration_hours = Column(Float, nullable=False)
    is_feasible = Column(Boolean, default=True)
    duration_validation = Column(Boolean, default=True)
    transport_type = Column(JSON)  # Stores TransportType object
    cargo = Column(JSON)  # Stores Cargo object
    total_cost = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    empty_driving = Column(JSON)  # Stores EmptyDriving object
    main_route = Column(JSON)  # Stores RouteSegment object
    timeline = Column(JSON)  # Stores List[TimelineEvent]

    # Relationship with offers
    offers = relationship("Offer", back_populates="route")

class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), nullable=True)
    countries = Column(JSON, nullable=True)
    regions = Column(JSON, nullable=True)
    cost_breakdown = Column(JSON, nullable=False)
    margin_percentage = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    currency = Column(SQLEnum('EUR', 'USD', 'GBP', name='currency'), nullable=False)
    status = Column(SQLEnum('DRAFT', 'PENDING', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offerstatus'), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    offer_metadata = Column(JSON, nullable=False, default={})

    # Relationship with route
    route = relationship("Route", back_populates="offers")

class CostItem(Base):
    """Model for storing cost calculation settings."""
    __tablename__ = 'cost_settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Fixed UUID handling
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False, default=1.0)
    currency = Column(String(3), nullable=False, default="EUR")
    is_enabled = Column(Boolean, nullable=False, default=True)
    description = Column(String(500))
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_cost_settings_name', 'name'),
        Index('ix_cost_settings_type_category', 'type', 'category'),
    )

class MetricLog(Base):
    __tablename__ = "metric_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    labels = Column(JSON)  # Stores Dict[str, str]
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

class MetricAggregate(Base):
    __tablename__ = "metric_aggregates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    period = Column(String, nullable=False)  # '1min', '5min', '1hour', '1day'
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    count = Column(Integer, nullable=False)
    sum = Column(Float, nullable=False)
    avg = Column(Float, nullable=False)
    min = Column(Float, nullable=False)
    max = Column(Float, nullable=False)
    p95 = Column(Float)  # 95th percentile
    labels = Column(JSON)  # Stores Dict[str, str]

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    condition = Column(String, nullable=False)  # 'gt', 'lt', 'eq'
    threshold = Column(Float, nullable=False)
    period = Column(String, nullable=False)  # Time window to evaluate
    labels_filter = Column(JSON)  # Optional label filters
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, ForeignKey('alert_rules.id'), nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    value = Column(Float, nullable=False)
    message = Column(String, nullable=False)
    resolved_at = Column(DateTime)
    
    # Relationship with alert rule
    rule = relationship("AlertRule")
