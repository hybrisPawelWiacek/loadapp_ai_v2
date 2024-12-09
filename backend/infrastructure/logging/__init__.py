"""
Centralized logging configuration for the LoadApp.AI application.
Provides consistent logging setup and formatters across the application.
"""

import structlog
import logging
import sys
from typing import Any, Dict, Optional

# Configure standard logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance with optional name.
    
    Args:
        name: Optional name for the logger (typically __name__)
        
    Returns:
        A configured structlog logger instance
    """
    return structlog.get_logger(name)

# Default logger instance
logger = get_logger(__name__)
