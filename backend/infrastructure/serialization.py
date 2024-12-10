"""Serialization utilities for JSON encoding/decoding."""

import json
from datetime import datetime
from uuid import UUID

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUIDs and datetimes."""
    
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_dumps(obj, **kwargs):
    """Wrapper around json.dumps that uses our custom encoder."""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

def json_loads(s, **kwargs):
    """Wrapper around json.loads."""
    return json.loads(s, **kwargs)
