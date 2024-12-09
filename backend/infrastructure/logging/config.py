"""
Configuration settings for the logging system.
"""

import os
from typing import Dict, Any

# Log levels
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Formatting settings
CONSOLE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
JSON_FORMAT = True  # Whether to output logs in JSON format

# Structlog specific settings
STRUCTLOG_CONFIG: Dict[str, Any] = {
    "processors": [
        "structlog.stdlib.add_log_level",
        "structlog.stdlib.add_logger_name",
        "structlog.processors.TimeStamper(fmt='iso')",
        "structlog.processors.StackInfoRenderer",
        "structlog.processors.format_exc_info",
        "structlog.processors.UnicodeDecoder",
        "structlog.processors.JSONRenderer" if JSON_FORMAT else "structlog.dev.ConsoleRenderer"
    ],
    "context_class": "dict",
    "logger_factory": "structlog.stdlib.LoggerFactory",
    "wrapper_class": "structlog.stdlib.BoundLogger",
    "cache_logger_on_first_use": True,
}

# Default context that will be included in all log messages
DEFAULT_CONTEXT = {
    "app": "loadapp.ai",
    "environment": os.getenv("ENVIRONMENT", "development"),
}
