import functools
import time
import structlog
from typing import Callable, Any

logger = structlog.get_logger(__name__)

def measure_service_operation_time(service: str, operation: str) -> Callable:
    """
    Decorator to measure and log the execution time of service operations.
    
    Args:
        service: Name of the service (e.g., 'RouteService', 'CostService')
        operation: Name of the operation being measured
        
    Returns:
        Decorated function that logs timing metrics
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log metric
                logger.info(
                    "metric_recorded",
                    metric_name="service_operation_time",
                    value=duration,
                    labels={
                        "service": service,
                        "operation": operation
                    },
                    average=duration
                )
                
                return result
                
            except Exception as e:
                # Still record timing even if operation failed
                duration = time.time() - start_time
                logger.error(
                    "service_operation_failed",
                    metric_name="service_operation_time",
                    value=duration,
                    labels={
                        "service": service,
                        "operation": operation
                    },
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
                
        return wrapper
    return decorator
