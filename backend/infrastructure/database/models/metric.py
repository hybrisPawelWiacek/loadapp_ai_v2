from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..session import Base

class MetricLog(Base):
    """SQLAlchemy model for storing raw metric logs."""
    __tablename__ = "metric_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Additional metadata
    tags = Column(JSON, nullable=False, default=dict)
    source = Column(String)  # Source of the metric (e.g., 'route_service', 'offer_service')
    context = Column(JSON)  # Additional context for the metric

class MetricAggregate(Base):
    """SQLAlchemy model for storing aggregated metrics."""
    __tablename__ = "metric_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String, nullable=False)
    aggregation_type = Column(String, nullable=False)  # e.g., 'avg', 'sum', 'min', 'max'
    value = Column(Float, nullable=False)
    
    # Time range for the aggregation
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Metadata
    tags = Column(JSON, nullable=False, default=dict)
    sample_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AlertRule(Base):
    """SQLAlchemy model for alert rules."""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    metric_name = Column(String, nullable=False)
    
    # Alert conditions
    condition_type = Column(String, nullable=False)  # e.g., 'threshold', 'change_rate'
    threshold = Column(Float, nullable=False)
    comparison = Column(String, nullable=False)  # e.g., '>', '<', '>=', '<='
    
    # Alert settings
    is_enabled = Column(Boolean, nullable=False, default=True)
    severity = Column(String, nullable=False, default='medium')  # low, medium, high, critical
    cooldown_minutes = Column(Integer, nullable=False, default=60)
    
    # Additional configuration
    aggregation_window = Column(Integer)  # minutes to aggregate over before checking
    tags_filter = Column(JSON)  # filter metrics by tags
    notification_channels = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class AlertEvent(Base):
    """SQLAlchemy model for alert events."""
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey('alert_rules.id'), nullable=False)
    status = Column(String, nullable=False)  # triggered, resolved, acknowledged
    
    # Alert details
    triggered_value = Column(Float, nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Context
    context = Column(JSON, nullable=False, default=dict)
    notification_sent = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    alert_rule = relationship("AlertRule", backref="events")
