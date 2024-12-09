"""Tests for the performance metrics system."""
import pytest
import time
import threading
import concurrent.futures
from unittest.mock import patch, MagicMock
import structlog
from datetime import datetime

from backend.infrastructure.monitoring.performance_metrics import (
    PerformanceMetrics, MetricPoint, MetricSeries,
    measure_api_response_time, measure_db_query_time, measure_service_operation_time
)

@pytest.fixture
def metrics():
    """Create a fresh PerformanceMetrics instance for each test."""
    # Reset the singleton instance
    PerformanceMetrics._instance = None
    return PerformanceMetrics()

def test_singleton_pattern():
    """Test that PerformanceMetrics follows the singleton pattern."""
    metrics1 = PerformanceMetrics()
    metrics2 = PerformanceMetrics()
    assert metrics1 is metrics2

def test_metric_point_creation():
    """Test creation of individual metric points."""
    value = 1.5
    labels = {"test": "label"}
    point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels)
    
    assert point.value == value
    assert point.labels == labels
    assert isinstance(point.timestamp, datetime)

def test_metric_series_operations():
    """Test metric series aggregation and statistics."""
    series = MetricSeries(name="test_metric")
    values = [1.0, 2.0, 3.0]
    
    for value in values:
        series.add_point(value)
    
    assert series.total_count == 3
    assert series.total_value == 6.0
    assert series.average == 2.0
    assert len(series.points) == 3

@patch('time.time')
def test_timing_accuracy(mock_time):
    """Test that timing measurements are accurate."""
    metrics = PerformanceMetrics()
    
    # Mock time.time() to return controlled values
    mock_time.side_effect = [0.0, 1.5]  # Simulate 1.5 seconds elapsed
    
    @measure_service_operation_time(service="test", operation="op")
    def test_function():
        pass
    
    test_function()
    
    metric = metrics.get_metric_series("service_operation_time")
    assert len(metric.points) == 1
    assert metric.points[0].value == 1.5
    assert metric.points[0].labels == {"service": "test", "operation": "op"}

def test_error_handling():
    """Test that metrics are recorded even when operations fail."""
    metrics = PerformanceMetrics()
    
    @measure_service_operation_time(service="test", operation="error_op")
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    error_metric = metrics.get_metric_series("service_operation_time_error")
    assert len(error_metric.points) == 1
    assert error_metric.points[0].labels.get("error") == "Test error"

def test_thread_safety():
    """Test thread-safe metric collection under concurrent load."""
    metrics = PerformanceMetrics()
    num_threads = 10
    iterations_per_thread = 100
    
    def record_metrics():
        for _ in range(iterations_per_thread):
            metrics.record_metric("concurrent_test", 1.0, {"thread": threading.current_thread().name})
    
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=record_metrics)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    metric = metrics.get_metric_series("concurrent_test")
    assert metric.total_count == num_threads * iterations_per_thread

def test_decorator_integration():
    """Test integration of all metric decorators."""
    metrics = PerformanceMetrics()
    
    @measure_api_response_time("test_endpoint")
    def api_function():
        time.sleep(0.1)
        return "OK"
    
    @measure_db_query_time(query_type="select", table="test_table")
    def db_function():
        time.sleep(0.1)
        return []
    
    @measure_service_operation_time(service="test_service", operation="test_op")
    def service_function():
        time.sleep(0.1)
        return True
    
    api_function()
    db_function()
    service_function()
    
    assert metrics.get_metric_series("api_response_time") is not None
    assert metrics.get_metric_series("db_query_time") is not None
    assert metrics.get_metric_series("service_operation_time") is not None

@patch('backend.infrastructure.monitoring.performance_metrics.logger')
def test_structured_logging(mock_logger):
    """Test that metrics are properly logged with structlog."""
    metrics = PerformanceMetrics()
    metrics.record_metric("test_metric", 1.5, {"test": "label"})
    
    mock_logger.info.assert_called_with(
        "metric_recorded",
        metric_name="test_metric",
        value=1.5,
        labels={"test": "label"},
        average=1.5
    )

def test_high_concurrency_load():
    """Test system under high concurrency with ThreadPoolExecutor."""
    metrics = PerformanceMetrics()
    num_workers = 4
    num_tasks = 1000
    
    def concurrent_task(task_id):
        metrics.record_metric(
            "concurrent_load_test",
            0.1,
            {"task_id": str(task_id)}
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(concurrent_task, i) for i in range(num_tasks)]
        concurrent.futures.wait(futures)
    
    metric = metrics.get_metric_series("concurrent_load_test")
    assert metric.total_count == num_tasks
    
    # Verify no exceptions occurred
    for future in futures:
        assert not future.exception()

def test_memory_usage():
    """Test memory usage with large number of metrics."""
    metrics = PerformanceMetrics()
    num_metrics = 10000
    
    for i in range(num_metrics):
        metrics.record_metric(
            "memory_test",
            1.0,
            {"iteration": str(i)}
        )
    
    metric = metrics.get_metric_series("memory_test")
    assert metric.total_count == num_metrics
    
    # Basic memory leak check
    import sys
    memory_size = sys.getsizeof(metric.points)
    assert memory_size < 1024 * 1024  # Should be less than 1MB

def test_metric_labels_consistency():
    """Test consistency of metric labels across different collection methods."""
    metrics = PerformanceMetrics()
    
    # Direct recording
    metrics.record_metric("test", 1.0, {"method": "direct"})
    
    # Via decorator
    @measure_service_operation_time(service="test", operation="decorator")
    def decorated_function():
        pass
    
    decorated_function()
    
    # Check both metrics have required label fields
    direct_metric = metrics.get_metric_series("test")
    decorator_metric = metrics.get_metric_series("service_operation_time")
    
    assert all(point.labels for point in direct_metric.points)
    assert all(point.labels for point in decorator_metric.points)

def test_get_all_metrics():
    """Test retrieval of all collected metrics."""
    metrics = PerformanceMetrics()
    
    # Reset the metrics store
    metrics._metrics = {}
    
    # Record several different metrics
    metrics.record_metric("metric1", 1.0)
    metrics.record_metric("metric2", 2.0)
    metrics.record_metric("metric3", 3.0)
    
    all_metrics = metrics.get_all_metrics()
    
    assert len(all_metrics) == 3
    assert "metric1" in all_metrics
    assert "metric2" in all_metrics
    assert "metric3" in all_metrics
    assert all_metrics["metric1"].average == 1.0
    assert all_metrics["metric2"].average == 2.0
    assert all_metrics["metric3"].average == 3.0
