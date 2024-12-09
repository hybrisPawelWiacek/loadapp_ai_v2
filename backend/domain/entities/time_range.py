"""Time range entity for querying historical data."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TimeRange:
    """Represents a time range with start and end dates for querying historical data.
    
    If end_time is not provided, it defaults to the current time.
    If start_time is not provided, it defaults to 30 days before end_time.
    """
    start_time: datetime
    end_time: datetime

    @classmethod
    def create(cls, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> 'TimeRange':
        """Create a TimeRange with optional start and end times.
        
        Args:
            start_time: Optional start time. If None, defaults to 30 days before end_time
            end_time: Optional end time. If None, defaults to current time
            
        Returns:
            TimeRange instance with normalized start and end times
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        if start_time is None:
            # Default to 30 days before end_time
            from datetime import timedelta
            start_time = end_time - timedelta(days=30)
            
        return cls(start_time=start_time, end_time=end_time)

    def __post_init__(self):
        """Validate the time range after initialization."""
        if self.start_time > self.end_time:
            raise ValueError("start_time cannot be later than end_time")
