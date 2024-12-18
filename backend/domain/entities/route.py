from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID, uuid4
from .location import Location
from .timeline import TimelineEvent
from .cargo import Cargo, TransportType
from dateutil import tz

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
    timeline_events: List[TimelineEvent] = field(default_factory=list)  # For compatibility with route_service
    total_duration_hours: float = 0.0
    id: UUID = field(default_factory=uuid4)
    transport_type: Optional[TransportType] = None
    cargo: Optional[Cargo] = None
    is_feasible: bool = True
    duration_validation: bool = True
    total_cost: float = 0.0
    currency: str = "EUR"
    cost_breakdown: Dict = field(default_factory=dict)
    optimization_insights: Dict = field(default_factory=dict)
    last_calculated: Optional[datetime] = None

    def __post_init__(self):
        # Ensure id is a UUID object
        if isinstance(self.id, str):
            self.id = UUID(self.id)
            
        # Ensure timeline and timeline_events are synchronized
        if not self.timeline and self.timeline_events:
            self.timeline = self.timeline_events
        elif not self.timeline_events and self.timeline:
            self.timeline_events = self.timeline
            
        # Ensure datetimes are timezone-aware (UTC)
        if isinstance(self.pickup_time, datetime) and not self.pickup_time.tzinfo:
            self.pickup_time = self.pickup_time.replace(tzinfo=tz.tzutc())
        if isinstance(self.delivery_time, datetime) and not self.delivery_time.tzinfo:
            self.delivery_time = self.delivery_time.replace(tzinfo=tz.tzutc())
        if isinstance(self.last_calculated, datetime) and not self.last_calculated.tzinfo:
            self.last_calculated = self.last_calculated.replace(tzinfo=tz.tzutc())

    def to_dict(self) -> dict:
        """Convert Route to dictionary with proper datetime handling."""
        def convert_value(value):
            if isinstance(value, UUID):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat() if value else None
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
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                try:
                    result[key] = convert_value(value)
                except Exception as e:
                    # Log the error and skip the field instead of using str()
                    import structlog
                    logger = structlog.get_logger(__name__)
                    logger.warning("failed_to_convert_field",
                                 field=key,
                                 error=str(e),
                                 route_id=str(self.id))
                    continue
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'Route':
        """Create a Route instance from a dictionary."""
        # Convert nested objects
        origin = Location(
            address=data['origin']['address'],
            latitude=data['origin']['latitude'],
            longitude=data['origin']['longitude']
        ) if data.get('origin') else None

        destination = Location(
            address=data['destination']['address'],
            latitude=data['destination']['latitude'],
            longitude=data['destination']['longitude']
        ) if data.get('destination') else None

        # Convert datetime strings to datetime objects
        pickup_time = datetime.fromisoformat(data['pickup_time']) if data.get('pickup_time') else None
        delivery_time = datetime.fromisoformat(data['delivery_time']) if data.get('delivery_time') else None
        last_calculated = datetime.fromisoformat(data['last_calculated']) if data.get('last_calculated') else None

        # Convert cargo if present
        cargo = None
        if data.get('cargo'):
            cargo = Cargo(
                type=data['cargo']['type'],
                weight=float(data['cargo']['weight']),
                value=float(data['cargo']['value']),
                special_requirements=data['cargo'].get('special_requirements', [])
            )

        # Convert empty driving
        empty_driving = None
        if data.get('empty_driving'):
            ed = data['empty_driving']
            empty_driving = EmptyDriving(
                distance_km=float(ed.get('distance_km', 0.0)),
                duration_hours=float(ed.get('duration_hours', 0.0)),
                base_cost=float(ed.get('base_cost', 0.0)),
                country_segments=[
                    CountrySegment(**segment) for segment in ed.get('country_segments', [])
                ]
            )

        # Convert main route
        main_route = None
        if data.get('main_route'):
            mr = data['main_route']
            main_route = MainRoute(
                distance_km=float(mr.get('distance_km', 0.0)),
                duration_hours=float(mr.get('duration_hours', 0.0)),
                base_cost=float(mr.get('base_cost', 0.0)),
                country_segments=[
                    CountrySegment(**segment) for segment in mr.get('country_segments', [])
                ]
            )

        # Create the Route instance
        route = cls(
            id=UUID(data['id']) if isinstance(data.get('id'), str) else data.get('id', uuid4()),
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            empty_driving=empty_driving,
            main_route=main_route,
            timeline_events=data.get('timeline_events', []),
            timeline=data.get('timeline', []),
            total_duration_hours=float(data.get('total_duration_hours', 0.0)),
            transport_type=data.get('transport_type'),
            cargo=cargo,
            is_feasible=data.get('is_feasible', True),
            duration_validation=data.get('duration_validation', True),
            total_cost=float(data.get('total_cost', 0.0)),
            currency=data.get('currency', 'EUR'),
            cost_breakdown=data.get('cost_breakdown', {}),
            optimization_insights=data.get('optimization_insights', {}),
            last_calculated=last_calculated
        )

        return route
