from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from .location import Location
from .timeline import TimelineEvent
from .cargo import Cargo, TransportType

@dataclass
class CountrySegment:
    country: str
    distance_km: float = 0.0
    distance: float = 0.0  # Keep for backward compatibility
    duration_hours: float = 0.0

    def __post_init__(self):
        # Ensure distance_km and distance are synchronized
        if self.distance_km == 0.0 and self.distance > 0.0:
            self.distance_km = self.distance
        elif self.distance == 0.0 and self.distance_km > 0.0:
            self.distance = self.distance_km

@dataclass
class EmptyDriving:
    distance_km: float = 200.0
    duration_hours: float = 4.0
    country_segments: List[CountrySegment] = field(default_factory=list)
    base_cost: float = 100.0

@dataclass
class MainRoute:
    distance_km: float = 1000.0
    duration_hours: float = 10.0
    country_segments: List[CountrySegment] = field(default_factory=list)
    base_cost: float = 150.0

@dataclass
class Route:
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    empty_driving: EmptyDriving = field(default_factory=EmptyDriving)
    main_route: MainRoute = field(default_factory=MainRoute)
    timeline: List[TimelineEvent] = field(default_factory=list)
    total_duration_hours: float = 0.0
    id: UUID = field(default_factory=uuid4)
    transport_type: Optional[TransportType] = None
    cargo: Optional[Cargo] = None
    is_feasible: bool = True
    duration_validation: bool = True
    total_cost: float = 0.0
    currency: str = "EUR"

    def to_dict(self) -> dict:
        """Convert Route to dictionary with proper datetime handling."""
        def convert_value(value):
            if isinstance(value, UUID):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, (list, tuple)):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif hasattr(value, 'to_dict'):
                return value.to_dict()
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items() 
                       if not k.startswith('_')}
            return value

        # Convert all attributes using the helper function
        return {
            key: convert_value(value)
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
