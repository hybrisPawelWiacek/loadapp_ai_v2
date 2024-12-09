"""Usage data entity for tracking cost setting usage."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class UsageData:
    """Represents usage data for a cost setting.
    
    Attributes:
        timestamp: When the usage occurred
        value: The value used in the calculation
        user_id: Optional ID of the user who triggered the usage
        context: Additional context about the usage (e.g., route_id, calculation_type)
        metadata: Any additional metadata about the usage
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    value: float = field(default=0.0)
    user_id: Optional[str] = field(default=None)
    context: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the usage data to a dictionary format for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "user_id": self.user_id,
            "context": self.context,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageData':
        """Create a UsageData instance from a dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            value=float(data["value"]),
            user_id=data.get("user_id"),
            context=data.get("context", {}),
            metadata=data.get("metadata", {})
        )
