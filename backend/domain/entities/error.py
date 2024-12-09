from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class ServiceError:
    code: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
