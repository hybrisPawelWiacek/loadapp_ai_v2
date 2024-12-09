"""
Custom formatters for structlog that can be used to customize log output.
"""

from typing import Any, Dict
import json

def format_for_stackdriver(logger: str, level: str, event_dict: Dict[str, Any]) -> str:
    """
    Format log entries in a way that's compatible with Google Cloud Logging.
    
    Args:
        logger: Logger name
        level: Log level
        event_dict: Log event dictionary
        
    Returns:
        Formatted log string
    """
    # Add standard fields expected by Cloud Logging
    output = {
        "severity": level.upper(),
        "logger": logger,
        "message": event_dict.pop("event", ""),
        "timestamp": event_dict.pop("timestamp", None),
    }
    
    # Add any remaining fields as extra context
    if event_dict:
        output["context"] = event_dict
        
    return json.dumps(output)

def format_for_console(logger: str, level: str, event_dict: Dict[str, Any]) -> str:
    """
    Format log entries for human-readable console output.
    
    Args:
        logger: Logger name
        level: Log level
        event_dict: Log event dictionary
        
    Returns:
        Formatted log string
    """
    timestamp = event_dict.pop("timestamp", "")
    event = event_dict.pop("event", "")
    
    # Format the context data
    context = ""
    if event_dict:
        context = " ".join(f"{k}={v}" for k, v in sorted(event_dict.items()))
        context = f" [{context}]"
    
    return f"{timestamp} {level:8} {logger}: {event}{context}"
