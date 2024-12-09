from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .db_setup import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
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

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String, ForeignKey('routes.id'), nullable=False)
    total_cost = Column(Float, nullable=False)
    margin = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    fun_fact = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    cost_breakdown = Column(JSON)  # Stores Dict[str, float]

    # Relationship with route
    route = relationship("Route", back_populates="offers")

class CostSetting(Base):
    __tablename__ = "cost_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    base_value = Column(Float, nullable=False)
    multiplier = Column(Float, default=1.0)
    currency = Column(String, default="EUR")
    is_enabled = Column(Boolean, default=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
