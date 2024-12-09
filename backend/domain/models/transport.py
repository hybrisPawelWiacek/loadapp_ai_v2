from dataclasses import dataclass, field
from typing import List, Dict, Optional
from uuid import uuid4

@dataclass
class TransportCapacity:
    max_weight: float
    max_volume: float

@dataclass
class TransportType:
    name: str = ""
    capacity: TransportCapacity = None
    restrictions: List[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        if self.capacity is None:
            self.capacity = TransportCapacity(max_weight=0, max_volume=0)
        if self.restrictions is None:
            self.restrictions = []
        if isinstance(self.capacity, dict):
            self.capacity = TransportCapacity(**self.capacity)

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str

@dataclass
class Cargo:
    type: str
    weight: float
    value: float
    special_requirements: List[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        if self.special_requirements is None:
            self.special_requirements = []

@dataclass
class RouteSegment:
    distance_km: float
    duration_hours: float
    country_segments: List[Dict[str, float]] = field(default_factory=list)

@dataclass
class EmptyDriving:
    distance_km: float = 200.0
    duration_hours: float = 4.0

@dataclass
class TimelineEvent:
    event_type: str
    location: Location
    timestamp: str
    description: str

@dataclass
class Route:
    id: str
    origin: Location
    destination: Location
    distance: float
    duration: float
    total_duration_hours: float = 0.0  # Total duration including stops
    is_feasible: bool = True
    duration_validation: bool = True
    transport_type: Optional[TransportType] = None
    cargo: Optional[Cargo] = None
    pickup_time: str = ""
    delivery_time: str = ""
    total_cost: float = 0.0
    currency: str = "USD"
    empty_driving: EmptyDriving = field(default_factory=EmptyDriving)
    main_route: RouteSegment = None
    timeline: List[TimelineEvent] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.origin, dict):
            self.origin = Location(**self.origin)
        if isinstance(self.destination, dict):
            self.destination = Location(**self.destination)
        if isinstance(self.transport_type, dict):
            self.transport_type = TransportType(**self.transport_type)
        if isinstance(self.cargo, dict):
            self.cargo = Cargo(**self.cargo)
        if not self.total_duration_hours:
            self.total_duration_hours = self.duration  # Default to route duration if not specified
        if self.main_route is None:
            self.main_route = RouteSegment(
                distance_km=self.distance,
                duration_hours=self.duration,
                country_segments=[{"country": "Germany", "distance": self.distance}]
            )
        if not self.timeline:
            self.timeline = [
                TimelineEvent(
                    event_type="pickup",
                    location=self.origin,
                    timestamp=self.pickup_time,
                    description=f"Pickup at {self.origin.address}"
                ),
                TimelineEvent(
                    event_type="delivery",
                    location=self.destination,
                    timestamp=self.delivery_time,
                    description=f"Delivery at {self.destination.address}"
                )
            ]
