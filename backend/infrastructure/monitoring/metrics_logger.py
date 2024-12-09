"""
MetricsLogger system for aggregating, persisting, and querying metrics data.
Provides functionality for periodic aggregation, data buffering, and alert monitoring.
"""
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Union, Any
import asyncio
import threading
import structlog
from collections import defaultdict
import numpy as np
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from ..database.models import MetricLog, MetricAggregate, AlertRule, AlertEvent
from ..database.config import SessionLocal
from .performance_metrics import PerformanceMetrics, MetricPoint, MetricSeries

logger = structlog.get_logger(__name__)

class MetricsBuffer:
    """Thread-safe buffer for storing metrics before batch persistence."""
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def add(self, metric: Dict[str, Any]) -> bool:
        """Add a metric to the buffer. Returns True if buffer is full."""
        with self._lock:
            self._buffer.append(metric)
            return len(self._buffer) >= self.max_size
    
    def get_and_clear(self) -> List[Dict[str, Any]]:
        """Get all metrics from the buffer and clear it."""
        with self._lock:
            metrics = self._buffer.copy()
            self._buffer.clear()
            return metrics

class MetricsLogger:
    """
    Handles metric aggregation, persistence, and alerting.
    Thread-safe singleton that integrates with PerformanceMetrics.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the metrics logger."""
        self.buffer = MetricsBuffer()
        self.performance_metrics = PerformanceMetrics()
        self._flush_task = None
        self._aggregate_task = None
        self._alert_task = None
        
        # Initialize aggregation periods
        self.aggregation_periods = {
            "1min": timedelta(minutes=1),
            "5min": timedelta(minutes=5),
            "1hour": timedelta(hours=1),
            "1day": timedelta(days=1)
        }
    
    async def start(self):
        """Start background tasks for metrics processing."""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._periodic_flush())
        if self._aggregate_task is None:
            self._aggregate_task = asyncio.create_task(self._periodic_aggregate())
        if self._alert_task is None:
            self._alert_task = asyncio.create_task(self._check_alerts())
    
    async def stop(self):
        """Stop background tasks and flush remaining metrics."""
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None
        if self._aggregate_task:
            self._aggregate_task.cancel()
            self._aggregate_task = None
        if self._alert_task:
            self._alert_task.cancel()
            self._alert_task = None
        
        # Flush remaining metrics
        await self._flush_metrics()
    
    def log_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Log a metric value with optional labels."""
        metric = {
            "name": name,
            "value": value,
            "labels": labels or {},
            "timestamp": datetime.now(pytz.UTC)
        }
        
        if self.buffer.add(metric):
            asyncio.create_task(self._flush_metrics())
    
    async def _periodic_flush(self, interval: int = 60):
        """Periodically flush metrics to storage."""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._flush_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("periodic_flush_error", error=str(e))
    
    async def _flush_metrics(self):
        """Flush buffered metrics to the database."""
        metrics = self.buffer.get_and_clear()
        if not metrics:
            return
        
        try:
            db = SessionLocal()
            try:
                db_metrics = [
                    MetricLog(
                        name=m["name"],
                        value=m["value"],
                        labels=m["labels"],
                        timestamp=m["timestamp"]
                    )
                    for m in metrics
                ]
                db.add_all(db_metrics)
                db.commit()
                
                logger.info(
                    "metrics_flushed",
                    count=len(metrics)
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(
                "metrics_flush_error",
                error=str(e),
                metric_count=len(metrics)
            )
    
    async def _periodic_aggregate(self, interval: int = 300):
        """Periodically aggregate metrics."""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._aggregate_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("periodic_aggregate_error", error=str(e))
    
    async def _aggregate_metrics(self):
        """Aggregate metrics for different time periods."""
        now = datetime.now(pytz.UTC)
        db = SessionLocal()
        try:
            for period_name, period_delta in self.aggregation_periods.items():
                start_time = now - period_delta
                
                # Query raw metrics for the period
                metrics = db.query(MetricLog).filter(
                    MetricLog.timestamp > start_time
                ).all()
                
                # Group metrics by name and labels
                grouped_metrics = defaultdict(list)
                for metric in metrics:
                    key = (metric.name, str(sorted(metric.labels.items())))
                    grouped_metrics[key].append(metric.value)
                
                # Calculate aggregates for each group
                for (name, labels_str), values in grouped_metrics.items():
                    values_array = np.array(values)
                    labels = dict(eval(labels_str))
                    
                    aggregate = MetricAggregate(
                        name=name,
                        period=period_name,
                        start_time=start_time,
                        end_time=now,
                        count=len(values),
                        sum=float(np.sum(values_array)),
                        avg=float(np.mean(values_array)),
                        min=float(np.min(values_array)),
                        max=float(np.max(values_array)),
                        p95=float(np.percentile(values_array, 95)),
                        labels=labels
                    )
                    db.add(aggregate)
            
            db.commit()
            logger.info("metrics_aggregated", period_count=len(self.aggregation_periods))
        except Exception as e:
            logger.error("aggregate_metrics_error", error=str(e))
            db.rollback()
        finally:
            db.close()
    
    async def _check_alerts(self, interval: int = 60):
        """Periodically check alert conditions."""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._evaluate_alerts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("check_alerts_error", error=str(e))
    
    async def _evaluate_alerts(self, test_session: Session = None):
        """Evaluate all alert rules against recent metrics."""
        db = test_session if test_session else SessionLocal()
        try:
            # Get active alert rules and keep them in the session
            rules = list(db.query(AlertRule).filter_by(enabled=True).all())
            
            for rule in rules:
                # Get any existing unresolved alerts for this rule
                existing_alert = (
                    db.query(AlertEvent)
                    .filter(
                        and_(
                            AlertEvent.rule_id == rule.id,
                            AlertEvent.resolved_at.is_(None)
                        )
                    )
                    .with_for_update()  # Lock the row for update
                    .first()
                )
                
                # Get the most recent aggregate for the rule's period
                aggregate = (
                    db.query(MetricAggregate)
                    .filter(
                        and_(
                            MetricAggregate.name == rule.metric_name,
                            MetricAggregate.period == rule.period
                        )
                    )
                    .order_by(
                        MetricAggregate.end_time.desc(),  # Order by end_time in descending order
                        MetricAggregate.id.desc()  # Then by id in descending order to get the most recently created
                    )
                    .first()
                )
                
                if not aggregate:
                    continue
                
                # Check if labels match the filter
                if rule.labels_filter:
                    if not all(
                        aggregate.labels.get(k) == v
                        for k, v in rule.labels_filter.items()
                    ):
                        continue
                
                # Evaluate the condition
                value = aggregate.avg  # Use average by default
                triggered = False
                
                if rule.condition == "gt":
                    triggered = value > rule.threshold
                elif rule.condition == "lt":
                    triggered = value < rule.threshold
                elif rule.condition == "eq":
                    triggered = abs(value - rule.threshold) < 0.0001
                
                logger.info(
                    "alert_evaluation",
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    value=value,
                    threshold=rule.threshold,
                    triggered=triggered,
                    has_existing_alert=existing_alert is not None,
                    end_time=aggregate.end_time,
                    labels=aggregate.labels,
                    aggregate_id=aggregate.id
                )
                
                if triggered and not existing_alert:
                    # Create new alert only if triggered and no existing alert
                    alert = AlertEvent(
                        rule_id=rule.id,
                        value=value,
                        message=f"{rule.name}: {rule.metric_name} is {rule.condition} {rule.threshold} (current value: {value})"
                    )
                    db.add(alert)
                    db.commit()  # Commit changes to create the alert
                    logger.warning(
                        "alert_triggered",
                        rule_name=rule.name,
                        metric_name=rule.metric_name,
                        value=value,
                        threshold=rule.threshold,
                        end_time=aggregate.end_time,
                        aggregate_id=aggregate.id
                    )
                elif not triggered and existing_alert:
                    # Resolve existing alert only if not triggered
                    existing_alert.resolved_at = datetime.now(pytz.UTC)
                    db.add(existing_alert)  # Explicitly add the modified alert back to session
                    db.commit()  # Commit changes to resolve the alert
                    logger.info(
                        "alert_resolved",
                        rule_name=rule.name,
                        metric_name=rule.metric_name,
                        value=value,
                        threshold=rule.threshold,
                        end_time=aggregate.end_time,
                        aggregate_id=aggregate.id
                    )
            
        except Exception as e:
            logger.error("evaluate_alerts_error", error=str(e))
            db.rollback()
            raise  # Re-raise the exception for testing
        finally:
            if not test_session:  # Only close if we created our own session
                db.close()
    
    def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: str,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricAggregate]:
        """Query aggregated metrics for a specific period."""
        db = SessionLocal()
        try:
            query = (
                db.query(MetricAggregate)
                .filter(
                    and_(
                        MetricAggregate.name == metric_name,
                        MetricAggregate.period == period,
                        MetricAggregate.start_time >= start_time,
                        MetricAggregate.end_time <= end_time
                    )
                )
            )
            
            if labels:
                # Filter by labels using JSON containment
                for key, value in labels.items():
                    query = query.filter(
                        MetricAggregate.labels.contains({key: value})
                    )
            
            return query.order_by(MetricAggregate.start_time).all()
        finally:
            db.close()
    
    def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        period: str,
        labels_filter: Optional[Dict[str, str]] = None
    ) -> AlertRule:
        """Create a new alert rule."""
        if condition not in ["gt", "lt", "eq"]:
            raise ValueError("Invalid condition. Must be one of: gt, lt, eq")
        
        if period not in self.aggregation_periods:
            raise ValueError(f"Invalid period. Must be one of: {', '.join(self.aggregation_periods.keys())}")
        
        db = SessionLocal()
        try:
            rule = AlertRule(
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                period=period,
                labels_filter=labels_filter
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)
            return rule
        finally:
            db.close()
    
    def get_active_alerts(self) -> List[AlertEvent]:
        """Get all unresolved alert events."""
        db = SessionLocal()
        try:
            return (
                db.query(AlertEvent)
                .filter(AlertEvent.resolved_at.is_(None))
                .order_by(AlertEvent.triggered_at.desc())
                .all()
            )
        finally:
            db.close()
