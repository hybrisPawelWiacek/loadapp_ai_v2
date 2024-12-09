"""
MetricsLogger system for aggregating, persisting, and querying metrics data.
Provides functionality for periodic aggregation, data buffering, and alert monitoring.
"""
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Union, Any
import asyncio
import threading
from collections import defaultdict
import numpy as np
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from ..database.models import MetricLog, MetricAggregate, AlertRule, AlertEvent
from ..database.config import SessionLocal
from .performance_metrics import PerformanceMetrics, MetricPoint, MetricSeries
from ..logging import logger

# Get a logger instance with metrics context
logger = logger.bind(
    component="metrics_logger",
    service="monitoring"
)

class MetricsLogger:
    """Handles metric aggregation, persistence, and alerting.
    Thread-safe singleton that integrates with PerformanceMetrics."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, flush_interval: int = 60):
        self.metrics_buffer: List[Dict] = []
        self.flush_interval = flush_interval
        self.running = False
        self.buffer_lock = threading.Lock()
        self._flush_task = None
        
        # Get or create event loop
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        self.aggregation_periods = ["1h", "1d", "7d", "30d"]
        
        # Initialize logger with instance context
        self.logger = logger.bind(
            instance_id=id(self),
            buffer_size=len(self.metrics_buffer)
        )
        self.logger.info("metrics_logger_initialized")
    
    def start(self):
        """Start background tasks for metrics processing."""
        if not self.running:
            self.running = True
            if not self._flush_task or self._flush_task.done():
                self._flush_task = self.loop.create_task(self._periodic_flush())
            self._aggregate_task = self.loop.create_task(self._periodic_aggregate())
            self._alert_task = self.loop.create_task(self._check_alerts())
            self.logger.info("background_tasks_started")
    
    def stop(self):
        """Stop background tasks and flush remaining metrics."""
        self.running = False
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        if self._aggregate_task and not self._aggregate_task.done():
            self._aggregate_task.cancel()
        if self._alert_task and not self._alert_task.done():
            self._alert_task.cancel()
        self.flush()  # Final flush
        self.logger.info("background_tasks_stopped")
    
    def log_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        """Log a metric value with optional labels."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric = {
            "name": name,
            "value": value,
            "labels": labels or {},
            "timestamp": timestamp.isoformat()
        }
        
        with self.buffer_lock:
            self.metrics_buffer.append(metric)
            self.logger.debug("metric_logged", 
                           metric_name=name, 
                           value=value, 
                           labels=labels,
                           buffer_size=len(self.metrics_buffer))
    
    async def _periodic_flush(self):
        """Periodically flush metrics to storage."""
        while self.running:
            await asyncio.sleep(self.flush_interval)
            self.flush()
            self.logger.info("metrics_flushed",
                          count=len(self.metrics_buffer),
                          first_timestamp=self.metrics_buffer[0]["timestamp"],
                          last_timestamp=self.metrics_buffer[-1]["timestamp"])
    
    def flush(self):
        """Flush buffered metrics to the database."""
        with self.buffer_lock:
            if not self.metrics_buffer:
                return
            
            session = SessionLocal()
            try:
                metrics_to_flush = self.metrics_buffer[:]
                self.metrics_buffer.clear()
                
                for metric in metrics_to_flush:
                    log_entry = MetricLog(
                        name=metric["name"],
                        value=metric["value"],
                        labels=metric["labels"],
                        timestamp=datetime.fromisoformat(metric["timestamp"])
                    )
                    session.add(log_entry)
                
                session.commit()
            except Exception as e:
                self.logger.error("flush_metrics_error",
                               error=str(e),
                               metrics_count=len(self.metrics_buffer))
                session.rollback()
            finally:
                session.close()
    
    async def _periodic_aggregate(self, interval: int = 300):
        """Periodically aggregate metrics."""
        while self.running:
            await asyncio.sleep(interval)
            await self._aggregate_metrics()
    
    async def _aggregate_metrics(self):
        """Aggregate metrics for different time periods."""
        now = datetime.utcnow()
        session = SessionLocal()
        try:
            for period_name in self.aggregation_periods:
                start_time = now - timedelta(hours=int(period_name[:-1]))
                
                # Query raw metrics for the period
                metrics = session.query(MetricLog).filter(
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
                    session.add(aggregate)
            
            session.commit()
            self.logger.info("metrics_aggregated", 
                          period_count=len(self.aggregation_periods))
        except Exception as e:
            self.logger.error("aggregate_metrics_error", 
                           error=str(e))
            session.rollback()
        finally:
            session.close()
    
    async def _check_alerts(self, interval: int = 60):
        """Periodically check alert conditions."""
        while self.running:
            await asyncio.sleep(interval)
            await self._evaluate_alerts()
    
    async def _evaluate_alerts(self, test_session: Session = None):
        """Evaluate all alert rules against recent metrics."""
        session = test_session if test_session else SessionLocal()
        try:
            # Get active alert rules and keep them in the session
            rules = list(session.query(AlertRule).filter_by(enabled=True).all())
            
            for rule in rules:
                # Get any existing unresolved alerts for this rule
                existing_alert = (
                    session.query(AlertEvent)
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
                    session.query(MetricAggregate)
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
                
                self.logger.info(
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
                    session.add(alert)
                    session.commit()  # Commit changes to create the alert
                    self.logger.warning(
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
                    existing_alert.resolved_at = datetime.utcnow()
                    session.add(existing_alert)  # Explicitly add the modified alert back to session
                    session.commit()  # Commit changes to resolve the alert
                    self.logger.info(
                        "alert_resolved",
                        rule_name=rule.name,
                        metric_name=rule.metric_name,
                        value=value,
                        threshold=rule.threshold,
                        end_time=aggregate.end_time,
                        aggregate_id=aggregate.id
                    )
            
        except Exception as e:
            self.logger.error("evaluate_alerts_error", 
                           error=str(e))
            session.rollback()
            raise  # Re-raise the exception for testing
        finally:
            if not test_session:  # Only close if we created our own session
                session.close()
    
    def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: str,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricAggregate]:
        """Query aggregated metrics for a specific period."""
        session = SessionLocal()
        try:
            query = (
                session.query(MetricAggregate)
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
            session.close()
    
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
            raise ValueError(f"Invalid period. Must be one of: {', '.join(self.aggregation_periods)}")
        
        session = SessionLocal()
        try:
            rule = AlertRule(
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                period=period,
                labels_filter=labels_filter
            )
            session.add(rule)
            session.commit()
            session.refresh(rule)
            return rule
        finally:
            session.close()
    
    def get_active_alerts(self) -> List[AlertEvent]:
        """Get all unresolved alert events."""
        session = SessionLocal()
        try:
            return (
                session.query(AlertEvent)
                .filter(AlertEvent.resolved_at.is_(None))
                .order_by(AlertEvent.triggered_at.desc())
                .all()
            )
        finally:
            session.close()

    def __del__(self):
        """Ensure background tasks are stopped on cleanup."""
        self.stop()
