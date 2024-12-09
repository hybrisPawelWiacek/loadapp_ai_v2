from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Optional
import structlog
from ..entities import (
    Route, Location, TransportType, Cargo, TimelineEvent,
    EmptyDriving, MainRoute, CountrySegment
)

logger = structlog.get_logger(__name__)

class RoutePlanningService:
    def __init__(self):
        self.logger = logger.bind(service="RoutePlanningService")

    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None
    ) -> Route:
        """Calculate a route with mocked data according to PoC requirements."""
        self.logger.info(
            "calculating_route",
            origin=origin.address,
            destination=destination.address
        )

        # Create route object
        route = Route(
            id=str(uuid4()),
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            cargo=cargo,
            transport_type=transport_type,
            total_duration_hours=10.0  # Mock duration in hours
        )

        # Add empty driving and main route details
        route.empty_driving.distance_km = 200.0
        route.empty_driving.duration_hours = 4.0
        route.empty_driving.country_segments = [
            CountrySegment(country="Germany", distance_km=200.0)
        ]
        route.empty_driving.base_cost = 100.0

        route.main_route.distance_km = 1000.0
        route.main_route.duration_hours = 10.0
        route.main_route.country_segments = [
            CountrySegment(country="Germany", distance_km=1000.0)
        ]
        route.main_route.base_cost = 150.0

        # Add timeline events
        route.timeline = [
            TimelineEvent(
                type="START",
                time=route.pickup_time,
                location=route.origin
            ),
            TimelineEvent(
                type="PICKUP",
                time=route.pickup_time + timedelta(hours=1),
                location=route.origin
            ),
            TimelineEvent(
                type="DELIVERY",
                time=route.delivery_time - timedelta(hours=1),
                location=route.destination
            ),
            TimelineEvent(
                type="END",
                time=route.delivery_time,
                location=route.destination
            )
        ]

        self.logger.info(
            "route_calculated",
            route_id=str(route.id),
            total_duration=route.total_duration_hours
        )

        return route
