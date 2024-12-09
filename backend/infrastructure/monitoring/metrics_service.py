"""Service layer for metrics tracking and monitoring."""
from typing import Dict, Optional, Any
from datetime import datetime
from ..logging import logger

class MetricsService:
    """Service for tracking and monitoring application metrics."""

    def __init__(self):
        """Initialize the metrics service."""
        self.logger = logger.bind(service="metrics_service")
        self._gauges = {}
        self._counters = {}
        self._histograms = {}

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric."""
        key = self._get_metric_key(name, labels)
        self._gauges[key] = value
        self.logger.debug("gauge_recorded", name=name, value=value, labels=labels)

    def counter(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._get_metric_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        self.logger.debug("counter_incremented", name=name, value=value, labels=labels)

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        key = self._get_metric_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self.logger.debug("histogram_recorded", name=name, value=value, labels=labels)

    def _get_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Generate a unique key for a metric based on its name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def track_route_calculation(self, duration_ms: float, route_type: str, success: bool,
                              additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Track route calculation performance and outcomes."""
        labels = {
            "type": route_type,
            "success": str(success).lower(),
            **(additional_context or {})
        }
        
        self.histogram("route_calculation_duration_ms", duration_ms, labels)
        self.counter("route_calculations_total", 1, labels)
        
        if success:
            self.counter("route_calculations_success", 1, labels)
        else:
            self.counter("route_calculations_failure", 1, labels)

    def track_cost_calculation(self, duration_ms: float, cost_type: str, success: bool,
                             additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Track cost calculation performance and outcomes."""
        labels = {
            "type": cost_type,
            "success": str(success).lower(),
            **(additional_context or {})
        }
        
        self.histogram("cost_calculation_duration_ms", duration_ms, labels)
        self.counter("cost_calculations_total", 1, labels)
        
        if success:
            self.counter("cost_calculations_success", 1, labels)
        else:
            self.counter("cost_calculations_failure", 1, labels)
