from dataclasses import dataclass, field
from datetime import datetime
from .location import Location

@dataclass
class TimelineEvent:
    type: str = field(default="")  # For backward compatibility
    event_type: str = field(default="")  # New field
    time: datetime = field(default_factory=datetime.now)
    location: Location = field(default_factory=Location)
    planned_time: datetime = field(default_factory=datetime.now)
    duration_minutes: int = field(default=0)
    description: str = field(default="")
    is_required: bool = field(default=True)

    def __post_init__(self):
        # Handle event_type being passed in constructor
        if not self.type and self.event_type:
            self.type = self.event_type
        elif not self.event_type and self.type:
            self.event_type = self.type
        
        # If time is not set but planned_time is, use planned_time
        if not self.time and self.planned_time:
            self.time = self.planned_time

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "event_type": self.event_type,
            "time": self.time.isoformat(),
            "planned_time": self.planned_time.isoformat(),
            "location": self.location.to_dict(),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "is_required": self.is_required
        }
