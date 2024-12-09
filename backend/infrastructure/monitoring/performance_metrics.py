"""
Performance metrics system for monitoring and logging application performance.
Provides tools for measuring API response times, service operations, and database queries.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time
import functools
import structlog
import time

logger = structlog.get_logger()

@dataclass
class MetricPoint:
    """A single measurement of a metric."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSeries:
    """A series of measurements for a specific metric."""
    name: str
    points: List[MetricPoint] = field(default_factory=list)
    total_count: int = 0
    total_value: float = 0.0
    
    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a new measurement point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
        self.total_count += 1
        self.total_value += value

    @property
    def average(self) -> float:
        """Calculate the average value across all points."""
        return self.total_value / self.total_count if self.total_count > 0 else 0.0

class PerformanceMetrics:
    """Thread-safe performance metrics collector and manager."""
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
        """Initialize the metrics storage."""
        self._metrics: Dict[str, MetricSeries] = {}
        self._metrics_lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a new metric measurement."""
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = MetricSeries(name=name)
            self._metrics[name].add_point(value, labels)
            
            # Log the metric
            logger.info(
                "metric_recorded",
                metric_name=name,
                value=value,
                labels=labels or {},
                average=self._metrics[name].average
            )
    
    def get_metric_series(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        with self._metrics_lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, MetricSeries]:
        """Get all metric series."""
        with self._metrics_lock:
            return dict(self._metrics)

def measure_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to measure execution time of a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                PerformanceMetrics().record_metric(
                    name=metric_name,
                    value=duration,
                    labels=labels
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_labels = {**(labels or {}), "error": str(e)}
                PerformanceMetrics().record_metric(
                    name=f"{metric_name}_error",
                    value=duration,
                    labels=error_labels
                )
                raise
        return wrapper
    return decorator

# Convenience functions for common metrics
def measure_api_response_time(endpoint: str):
    """Decorator specifically for measuring API endpoint response times."""
    return measure_time(
        metric_name="api_response_time",
        labels={"endpoint": endpoint}
    )

def measure_db_query_time(query_type: str, table: str):
    """Decorator specifically for measuring database query times."""
    return measure_time(
        metric_name="db_query_time",
        labels={"query_type": query_type, "table": table}
    )

def measure_service_operation_time(service: str, operation: str):
    """Decorator specifically for measuring service operation times."""
    return measure_time(
        metric_name="service_operation_time",
        labels={"service": service, "operation": operation}
    )
