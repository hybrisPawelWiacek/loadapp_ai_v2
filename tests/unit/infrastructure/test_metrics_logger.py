"""Tests for the MetricsLogger system."""
import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.infrastructure.monitoring.metrics_logger import (
    MetricsLogger,
    MetricsBuffer,
    MetricLog,
    MetricAggregate,
    AlertRule,
    AlertEvent
)
from backend.infrastructure.database.session import Base

# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    engine = create_engine(
        "postgresql://postgres@localhost:5432/loadapp_test",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def metrics_logger(db_session):
    """Create a MetricsLogger instance with mocked session."""
    with patch("backend.infrastructure.monitoring.metrics_logger.SessionLocal") as mock_session:
        mock_session.return_value = db_session
        logger = MetricsLogger()
        yield logger

class TestMetricsBuffer:
    def test_buffer_add_and_clear(self):
        """Test adding metrics to buffer and clearing them."""
        buffer = MetricsBuffer(max_size=2)
        metric1 = {"name": "test", "value": 1.0, "labels": {}}
        metric2 = {"name": "test", "value": 2.0, "labels": {}}
        
        # Add first metric - shouldn't trigger full condition
        assert not buffer.add(metric1)
        
        # Add second metric - should trigger full condition
        assert buffer.add(metric2)
        
        # Check buffer contents
        metrics = buffer.get_and_clear()
        assert len(metrics) == 2
        assert metrics[0]["value"] == 1.0
        assert metrics[1]["value"] == 2.0
        
        # Buffer should be empty after clear
        assert len(buffer.get_and_clear()) == 0

class TestMetricsLogger:
    @pytest.mark.asyncio
    async def test_log_and_flush_metrics(self, metrics_logger, db_session):
        """Test logging metrics and flushing to database."""
        # Log some test metrics
        metrics_logger.log_metric("test_metric", 1.0, {"label1": "value1"})
        metrics_logger.log_metric("test_metric", 2.0, {"label1": "value1"})
        
        # Force flush
        await metrics_logger._flush_metrics()
        
        # Verify metrics were stored
        logs = db_session.query(MetricLog).all()
        assert len(logs) == 2
        assert logs[0].name == "test_metric"
        assert logs[0].value == 1.0
        assert logs[0].labels == {"label1": "value1"}
    
    @pytest.mark.asyncio
    async def test_metric_aggregation(self, metrics_logger, db_session):
        """Test metric aggregation for different periods."""
        # Create test data
        now = datetime.now(timezone.utc)
        test_metrics = [
            MetricLog(
                name="test_metric",
                value=i,
                labels={"env": "test"},
                timestamp=now - timedelta(minutes=i)
            )
            for i in range(10)
        ]
        db_session.add_all(test_metrics)
        db_session.commit()
        
        # Run aggregation
        await metrics_logger._aggregate_metrics()
        
        # Check aggregates
        aggregates = db_session.query(MetricAggregate).filter_by(
            name="test_metric",
            period="5min"
        ).all()
        
        assert len(aggregates) > 0
        agg = aggregates[0]
        assert agg.name == "test_metric"
        assert agg.labels == {"env": "test"}
        assert agg.count > 0
        assert isinstance(agg.avg, float)
        assert isinstance(agg.p95, float)
    
    @pytest.mark.asyncio
    async def test_alert_evaluation(self, metrics_logger, db_session):
        """Test alert rule evaluation and event creation."""
        now = datetime.now(timezone.utc)
        
        # Create test alert rule
        rule = AlertRule(
            name="High Value Alert",
            metric_name="test_metric",
            condition="gt",
            threshold=5.0,
            period="5min",
            labels_filter={"env": "test"},
            enabled=True  # Make sure rule is enabled
        )
        db_session.add(rule)
        db_session.commit()  # Commit to ensure rule has an ID
        rule_id = rule.id  # Store rule ID for later comparison
        
        # Create test aggregate that should trigger alert
        agg = MetricAggregate(
            name="test_metric",
            period="5min",
            start_time=now - timedelta(minutes=5),
            end_time=now,
            count=1,
            sum=10.0,
            avg=10.0,
            min=10.0,
            max=10.0,
            p95=10.0,
            labels={"env": "test"}
        )
        db_session.add(agg)
        db_session.commit()
        
        # Evaluate alerts
        await metrics_logger._evaluate_alerts(test_session=db_session)
        
        # Check alert was created
        alerts = db_session.query(AlertEvent).all()
        assert len(alerts) == 1
        assert alerts[0].rule_id == rule_id
        assert alerts[0].value == 10.0
        assert alerts[0].resolved_at is None
        
        # Store the ID of the first alert
        first_alert_id = alerts[0].id
        
        # Create aggregate below threshold
        agg = MetricAggregate(
            name="test_metric",
            period="5min",
            start_time=now - timedelta(minutes=5),
            end_time=now,
            count=1,
            sum=2.0,
            avg=2.0,
            min=2.0,
            max=2.0,
            p95=2.0,
            labels={"env": "test"}
        )
        db_session.add(agg)
        db_session.commit()
        
        # Evaluate alerts again
        await metrics_logger._evaluate_alerts(test_session=db_session)
        db_session.commit()  # Ensure changes are committed
        
        # Query the alert directly and refresh it from the database
        alert = db_session.get(AlertEvent, first_alert_id)
        db_session.refresh(alert)  # Force refresh from database
        
        # Check alert was resolved
        assert alert.resolved_at is not None
        
        # Create another high value aggregate
        agg = MetricAggregate(
            name="test_metric",
            period="5min",
            start_time=now - timedelta(minutes=5),
            end_time=now,
            count=1,
            sum=15.0,
            avg=15.0,
            min=15.0,
            max=15.0,
            p95=15.0,
            labels={"env": "test"}
        )
        db_session.add(agg)
        db_session.commit()
        
        # Evaluate alerts one more time
        await metrics_logger._evaluate_alerts(test_session=db_session)
        db_session.commit()  # Ensure changes are committed
        
        # Query alerts with a fresh session to ensure we get the latest state
        alerts = db_session.query(AlertEvent).order_by(AlertEvent.triggered_at).all()
        db_session.refresh(alerts[1])  # Explicitly refresh the alert object
        
        # Check that a new alert was created
        assert len(alerts) == 2
        assert alerts[0].resolved_at is not None  # First alert should be resolved
        assert alerts[1].resolved_at is None  # New alert should be unresolved
        assert alerts[1].value == 15.0
    
    def test_query_metrics(self, metrics_logger, db_session):
        """Test querying aggregated metrics."""
        # Create test aggregates
        now = datetime.now(timezone.utc)
        aggs = [
            MetricAggregate(
                name="test_metric",
                period="5min",
                start_time=now - timedelta(minutes=i*5),
                end_time=now - timedelta(minutes=(i-1)*5),
                count=1,
                sum=float(i),
                avg=float(i),
                min=float(i),
                max=float(i),
                p95=float(i),
                labels={"env": "test"}
            )
            for i in range(1, 5)
        ]
        db_session.add_all(aggs)
        db_session.commit()
        
        # Query metrics
        results = metrics_logger.query_metrics(
            metric_name="test_metric",
            start_time=now - timedelta(minutes=20),
            end_time=now,
            period="5min",
            labels={"env": "test"}
        )
        
        assert len(results) == 4
        assert all(r.name == "test_metric" for r in results)
        assert all(r.period == "5min" for r in results)
        assert all(r.labels == {"env": "test"} for r in results)
    
    def test_create_alert_rule(self, metrics_logger, db_session):
        """Test creating alert rules."""
        rule = metrics_logger.create_alert_rule(
            name="Test Alert",
            metric_name="test_metric",
            condition="gt",
            threshold=5.0,
            period="5min",
            labels_filter={"env": "test"}
        )
        
        assert rule.id is not None
        assert rule.name == "Test Alert"
        assert rule.metric_name == "test_metric"
        assert rule.condition == "gt"
        assert rule.threshold == 5.0
        assert rule.period == "5min"
        assert rule.labels_filter == {"env": "test"}
        
        # Test invalid condition
        with pytest.raises(ValueError):
            metrics_logger.create_alert_rule(
                name="Invalid Alert",
                metric_name="test_metric",
                condition="invalid",
                threshold=5.0,
                period="5min"
            )
        
        # Test invalid period
        with pytest.raises(ValueError):
            metrics_logger.create_alert_rule(
                name="Invalid Alert",
                metric_name="test_metric",
                condition="gt",
                threshold=5.0,
                period="invalid"
            )
    
    @pytest.mark.asyncio
    async def test_background_tasks(self, metrics_logger):
        """Test starting and stopping background tasks."""
        # Start tasks
        await metrics_logger.start()
        assert metrics_logger._flush_task is not None
        assert metrics_logger._aggregate_task is not None
        assert metrics_logger._alert_task is not None
        
        # Stop tasks
        await metrics_logger.stop()
        assert metrics_logger._flush_task is None
        assert metrics_logger._aggregate_task is None
        assert metrics_logger._alert_task is None
    
    def test_get_active_alerts(self, metrics_logger, db_session):
        """Test retrieving active alerts."""
        # Create test alerts
        now = datetime.now(timezone.utc)
        alerts = [
            AlertEvent(
                rule_id=1,
                value=1.0,
                message="Test alert 1",
                triggered_at=now - timedelta(minutes=10)
            ),
            AlertEvent(
                rule_id=1,
                value=2.0,
                message="Test alert 2",
                triggered_at=now - timedelta(minutes=5),
                resolved_at=now  # This one is resolved
            ),
            AlertEvent(
                rule_id=2,
                value=3.0,
                message="Test alert 3",
                triggered_at=now
            )
        ]
        db_session.add_all(alerts)
        db_session.commit()
        
        active_alerts = metrics_logger.get_active_alerts()
        assert len(active_alerts) == 2  # Only unresolved alerts
        assert all(a.resolved_at is None for a in active_alerts)
        assert sorted([a.value for a in active_alerts]) == [1.0, 3.0]
