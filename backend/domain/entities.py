from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID, uuid4

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str

@dataclass
class TransportType:
    id: str
    name: str
    capacity: Dict
    restrictions: List[str]

@dataclass
class Cargo:
    id: str
    type: str
    weight: float
    value: float
    special_requirements: List[str]

@dataclass
class RouteSegment:
    distance_km: float
    duration_hours: float
    country_segments: List[Dict[str, float]]
    base_cost: float = 75.0  # Default base cost for empty driving

@dataclass
class TimelineEvent:
    event_type: str  # start, pickup, rest, border_crossing, delivery
    time: datetime
    location: Location
    duration: Optional[float] = None  # Duration in hours if applicable
    notes: Optional[str] = None

@dataclass
class Route:
    id: UUID = field(default_factory=uuid4)
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    transport_type: Optional[TransportType] = None
    cargo: Optional[Cargo] = None
    empty_driving: RouteSegment = field(default_factory=lambda: RouteSegment(
        distance_km=200.0,
        duration_hours=4.0,
        country_segments=[{"country": "Germany", "distance": 200.0}],
        base_cost=75.0
    ))
    main_route: RouteSegment = field(default_factory=lambda: RouteSegment(
        distance_km=1000.0,
        duration_hours=10.0,
        country_segments=[{"country": "Germany", "distance": 1000.0}],
        base_cost=150.0
    ))
    timeline: List[TimelineEvent] = field(default_factory=list)
    total_duration_hours: float = 0.0
    is_feasible: bool = True
    duration_validation: bool = True

@dataclass
class CostItem:
    type: str
    category: str
    base_value: float
    multiplier: float = 1.0
    is_enabled: bool = True
    description: str = ""
    id: UUID = field(default_factory=uuid4)

@dataclass
class Offer:
    id: UUID = field(default_factory=uuid4)
    route_id: UUID
    total_cost: float
    margin: float
    final_price: float
    cost_breakdown: Dict
    fun_fact: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
