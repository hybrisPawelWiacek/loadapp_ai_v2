from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from ..entities import Route, Location, Cargo, TransportType, EmptyDriving, MainRoute, TimelineEvent, CountrySegment

class RoutePlanningService:
    MAX_DAILY_DRIVING_HOURS = 9  # EU regulation
    REQUIRED_REST_AFTER_HOURS = 4.5  # EU regulation
    MIN_REST_DURATION_HOURS = 0.75  # 45 minutes
    LOADING_WINDOW_START = 6  # 6 AM
    LOADING_WINDOW_END = 22  # 10 PM
    
    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None
    ) -> Route:
        """
        Calculate a route between two locations with comprehensive timeline validation.

        Args:
            origin: Origin location
            destination: Destination location
            pickup_time: Pickup time (timezone-aware)
            delivery_time: Delivery time (timezone-aware)
            cargo: Optional cargo details
            transport_type: Optional transport type

        Returns:
            Route object with calculated details

        Raises:
            ValueError: If timeline constraints are violated
        """
        self._validate_basic_timeline(pickup_time, delivery_time)
        self._validate_loading_window(pickup_time)
        
        # Calculate segments
        empty_driving = self._calculate_empty_driving(origin, destination)
        main_route = self._calculate_main_route(origin, destination)
        
        # Validate total duration against timeline
        total_duration = empty_driving.duration_hours + main_route.duration_hours
        available_time = (delivery_time - pickup_time).total_seconds() / 3600
        
        if total_duration > self.MAX_DAILY_DRIVING_HOURS:
            raise ValueError(f"Exceeds maximum daily driving time of {self.MAX_DAILY_DRIVING_HOURS} hours")
            
        if total_duration > self.REQUIRED_REST_AFTER_HOURS:
            required_time = total_duration + self.MIN_REST_DURATION_HOURS
            if available_time < required_time:
                raise ValueError("Required rest period not possible within timeline")
        
        # Generate timeline
        timeline = self._generate_timeline(
            origin, destination, pickup_time, delivery_time,
            empty_driving, main_route
        )
        
        return Route(
            id=uuid4(),
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            transport_type=transport_type,
            cargo=cargo,
            empty_driving=empty_driving,
            main_route=main_route,
            timeline=timeline,
            total_duration_hours=total_duration,
            is_feasible=True,
            duration_validation=True
        )
    
    def _validate_basic_timeline(self, pickup_time: datetime, delivery_time: datetime):
        """Validate basic timeline constraints."""
        if delivery_time <= pickup_time:
            raise ValueError("Delivery time must be after pickup")
            
        if not pickup_time.tzinfo or not delivery_time.tzinfo:
            raise ValueError("Datetime objects must be timezone-aware")
    
    def _validate_loading_window(self, pickup_time: datetime):
        """Validate that loading occurs within allowed time window."""
        hour = pickup_time.hour
        if hour < self.LOADING_WINDOW_START or hour >= self.LOADING_WINDOW_END:
            raise ValueError("Loading time outside of allowed window (6 AM - 10 PM)")
    
    def _calculate_empty_driving(self, origin: Location, destination: Location) -> EmptyDriving:
        """Calculate empty driving segment."""
        return EmptyDriving(
            distance_km=200.0,  # Example value
            duration_hours=4.0,  # Example value
            base_cost=75.0,  # Example value
            country_segments=[
                CountrySegment(
                    country="Germany",
                    distance_km=200.0
                )
            ]
        )
    
    def _calculate_main_route(self, origin: Location, destination: Location) -> MainRoute:
        """Calculate main route segment."""
        return MainRoute(
            distance_km=700.0,  # Example value
            duration_hours=9.0,  # Example value
            base_cost=1050.0,  # Example value
            country_segments=[
                CountrySegment(
                    country="Germany",
                    distance_km=300.0
                ),
                CountrySegment(
                    country="Poland",
                    distance_km=400.0
                )
            ]
        )
    
    def _generate_timeline(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        empty_driving: EmptyDriving,
        main_route: MainRoute
    ) -> List[TimelineEvent]:
        """Generate timeline events for the route."""
        timeline = []
        
        # Start event
        timeline.append(TimelineEvent(
            event_type="start",
            time=pickup_time - timedelta(hours=empty_driving.duration_hours),
            location=origin
        ))
        
        # Pickup event
        timeline.append(TimelineEvent(
            event_type="pickup",
            time=pickup_time,
            location=origin,
            duration=0.5  # 30 minutes for loading
        ))
        
        # Calculate rest stops if needed
        current_time = pickup_time + timedelta(hours=0.5)  # After loading
        remaining_drive_time = main_route.duration_hours
        
        while remaining_drive_time > self.REQUIRED_REST_AFTER_HOURS:
            # Add rest stop
            rest_time = current_time + timedelta(hours=self.REQUIRED_REST_AFTER_HOURS)
            timeline.append(TimelineEvent(
                event_type="rest",
                time=rest_time,
                location=Location(  # Example rest location
                    latitude=(origin.latitude + destination.latitude) / 2,
                    longitude=(origin.longitude + destination.longitude) / 2,
                    address="Rest Area"
                ),
                duration=self.MIN_REST_DURATION_HOURS,
                notes="Required rest period"
            ))
            
            current_time = rest_time + timedelta(hours=self.MIN_REST_DURATION_HOURS)
            remaining_drive_time -= self.REQUIRED_REST_AFTER_HOURS
        
        # Delivery event
        timeline.append(TimelineEvent(
            event_type="delivery",
            time=delivery_time,
            location=destination,
            duration=0.5  # 30 minutes for unloading
        ))
        
        return timeline
