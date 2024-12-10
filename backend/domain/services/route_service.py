from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import structlog

from ...domain.entities.route import Route, EmptyDriving, MainRoute, CountrySegment, TimelineEvent
from ...domain.entities.cost_setting import CostSetting
from ...domain.entities.location import Location
from ...domain.entities.cargo import Cargo, TransportType
from ...domain.entities.timeline import TimelineEvent
from ...domain.exceptions import ValidationError as DomainValidationError, RouteValidationException
from ...domain.validators.cost_setting_validator import (
    CostSettingValidator,
    ValidationError as CostValidationError
)
from ...infrastructure.database.repositories.base_repository import BaseRepository
from ...infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from ...infrastructure.monitoring.metrics_service import MetricsService
from ...domain.services.cost_calculation_service import CostCalculationService

class TimelineValidationError(DomainValidationError):
    """Error raised when route timeline validation fails."""
    def __init__(self, message: str):
        super().__init__(message=message, field="timeline")

class RouteService:
    """Service for managing routes and their associated cost settings."""
    
    MAX_DAILY_DRIVING_HOURS = 9
    REQUIRED_REST_AFTER_HOURS = 4.5
    MIN_REST_DURATION_HOURS = 0.75
    LOADING_WINDOW_START = 6
    LOADING_WINDOW_END = 22

    def __init__(
            self,
            repository: BaseRepository,
            cost_settings_repository: CostSettingsRepository,
            cost_calculation_service: CostCalculationService,
            cost_validator: CostSettingValidator,
            metrics_service: MetricsService
        ):
        """Initialize the route service with required dependencies."""
        self.repository = repository
        self.cost_settings_repository = cost_settings_repository
        self.cost_calculation_service = cost_calculation_service
        self.cost_validator = cost_validator
        self.metrics_service = metrics_service
        self.logger = structlog.get_logger(__name__)

    def create_route(
        self,
        route: Route,
        cost_settings: List[CostSetting],
        validate_timeline: bool = True
    ) -> Route:
        """
        Create a new route with associated cost settings.
        
        Args:
            route: Route to create
            cost_settings: List of cost settings to associate with the route
            validate_timeline: Whether to perform timeline validation
            
        Returns:
            Created route with cost calculations
            
        Raises:
            RouteValidationException: If cost settings or timeline validation fails
        """
        try:
            self.logger.debug(
                "creating_route",
                route_id=route.id,
                route_id_type=type(route.id).__name__,
                cost_settings_count=len(cost_settings),
                cost_settings_ids=[str(s.id) for s in cost_settings],
                cost_settings_types=[s.type for s in cost_settings]
            )
            
            # Validate cost settings
            validation_errors = self.validate_route_cost_settings(cost_settings)
            
            # Validate timeline if requested
            if validate_timeline:
                self.logger.debug("validating_timeline", route_id=route.id)
                timeline_errors = self.validate_route_timeline(route)
                validation_errors.extend(timeline_errors)
            
            if validation_errors:
                raise RouteValidationException(validation_errors)

            # Calculate initial costs
            self.logger.debug(
                "calculating_costs",
                route_id=route.id,
                cost_settings_count=len(cost_settings)
            )
            cost_calculation = self.cost_calculation_service.calculate_route_cost(route)
            
            # Update route with cost information
            route.total_cost = cost_calculation["total_cost"]
            route.currency = cost_calculation["currency"]
            route.cost_breakdown = cost_calculation["cost_breakdown"]
            route.optimization_insights = cost_calculation["optimization_insights"]
            route.last_calculated = datetime.utcnow()
            
            # Add rest stops if needed
            if validate_timeline:
                route.timeline_events = self._calculate_rest_stops(route)
                route.has_rest_stops = True
                route.rest_stops_count = self._calculate_required_rest_stops(route.empty_driving.duration_hours + route.main_route.duration_hours)
                route.total_rest_duration = route.rest_stops_count * self.MIN_REST_DURATION_HOURS
            
            # Track metrics
            self.metrics_service.counter(
                "route.creation.success",
                labels={
                    "has_cost_settings": str(bool(cost_settings)),
                    "route_type": route.type if hasattr(route, 'type') else 'unknown',
                }
            )

            # Save route to database
            self.logger.debug("saving_route_to_database", route_id=route.id)
            saved_route = self.repository.create(route)
            self.logger.info("route_saved_successfully", route_id=route.id)
            
            return saved_route

        except Exception as e:
            self.logger.error(
                "route_creation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def update_route(
        self, route_id: UUID, updates: Dict, cost_settings: Optional[List[CostSetting]] = None
    ) -> Route:
        """
        Update an existing route and optionally its cost settings.
        
        Args:
            route_id: ID of the route to update
            updates: Dictionary of route updates
            cost_settings: Optional list of new cost settings
            
        Returns:
            Updated route
            
        Raises:
            RouteValidationException: If cost settings validation fails
        """
        try:
            route = self.repository.get_by_id(route_id)
            if not route:
                raise ValueError(f"Route not found: {route_id}")
            
            # Update route fields
            for key, value in updates.items():
                if hasattr(route, key):
                    setattr(route, key, value)
            
            # If cost settings provided, validate and update
            if cost_settings is not None:
                validation_errors = self.validate_route_cost_settings(cost_settings)
                if validation_errors:
                    raise RouteValidationException(validation_errors)
                
                # Recalculate costs
                cost_calculation = self.cost_calculation_service.calculate_route_cost(route)
                route.total_cost = cost_calculation["total_cost"]
                route.currency = cost_calculation["currency"]
                route.cost_breakdown = cost_calculation["cost_breakdown"]
                route.optimization_insights = cost_calculation["optimization_insights"]
                route.last_calculated = datetime.utcnow()
            
            updated_route = self.repository.update(route)
            
            # Track metrics
            self.metrics_service.counter(
                "route.update.success",
                labels={
                    "cost_settings_updated": str(cost_settings is not None),
                    "route_type": route.type if hasattr(route, 'type') else 'unknown'
                }
            )
            
            return updated_route
            
        except RouteValidationException:
            self.metrics_service.counter("route.update.validation_failure")
            raise
        except Exception as e:
            self.metrics_service.counter("route.update.error")
            self.logger.error("route_update_failed",
                            route_id=str(route_id),
                            error=str(e))
            raise

    def validate_route_cost_settings(
        self, cost_settings: List[CostSetting]
    ) -> List[CostValidationError]:
        """
        Validate cost settings for a route.
        
        Args:
            cost_settings: List of cost settings to validate
            
        Returns:
            List of validation errors (empty if validation passed)
        """
        try:
            validation_errors = []

            # Check if there are any cost settings
            if not cost_settings:
                validation_errors.append(CostValidationError(
                    setting_id=None,
                    code="NO_COST_SETTINGS",
                    message="No cost settings provided for route calculation"
                ))
                return validation_errors

            # Get current enabled settings for comparison
            enabled_settings = self.cost_settings_repository.get_enabled_cost_settings()
            
            # Validate individual settings
            validation_errors.extend(self.cost_validator.validate_all(cost_settings))
            
            # Additional route-specific validations
            required_types = {"fuel", "maintenance", "time"}  # Basic required types
            provided_types = {s.type for s in cost_settings if s.is_enabled}
            missing_types = required_types - provided_types
            
            if missing_types:
                validation_errors.append(CostValidationError(
                    setting_id=None,
                    code="MISSING_REQUIRED_TYPES",
                    message=f"Missing required cost types for route: {', '.join(missing_types)}",
                    context={"missing_types": list(missing_types)}
                ))
            
            # Track validation metrics
            self.metrics_service.gauge(
                "route.cost_settings.validation_errors",
                len(validation_errors)
            )
            
            return validation_errors
            
        except Exception as e:
            self.logger.error("cost_settings_validation_failed", error=str(e))
            raise

    def validate_route_timeline(self, route: Route) -> List[TimelineValidationError]:
        """
        Validate route timeline against EU regulations.
        
        Args:
            route: Route to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate timezone awareness
        if not route.pickup_time.tzinfo or not route.delivery_time.tzinfo:
            errors.append(TimelineValidationError("Datetime objects must be timezone-aware"))

        # Basic timeline validation
        if route.delivery_time <= route.pickup_time:
            errors.append(TimelineValidationError("Delivery time must be after pickup time"))

        # Loading window validation
        if not self._is_within_loading_window(route.pickup_time):
            errors.append(TimelineValidationError(
                f"Loading time outside of allowed window ({self.LOADING_WINDOW_START} AM - {self.LOADING_WINDOW_END} PM)"
            ))

        # Calculate total driving time and required rest periods
        total_duration = route.empty_driving.duration_hours + route.main_route.duration_hours
        required_rest_stops = self._calculate_required_rest_stops(total_duration)
        total_rest_time = required_rest_stops * self.MIN_REST_DURATION_HOURS
        
        # Calculate total required time including rest stops
        total_required_time = total_duration + total_rest_time + 1  # +1 hour for loading/unloading
        available_time = (route.delivery_time - route.pickup_time).total_seconds() / 3600
        
        if available_time < total_required_time:
            errors.append(TimelineValidationError(
                f"Timeline too tight. Need {total_required_time:.1f} hours (including {required_rest_stops} rest stops) but only {available_time:.1f} hours available"
            ))

        return errors

    def _is_within_loading_window(self, time: datetime) -> bool:
        """Check if time is within loading window."""
        hour = time.hour
        return self.LOADING_WINDOW_START <= hour <= self.LOADING_WINDOW_END

    def _calculate_required_rest_stops(self, total_hours: float) -> int:
        """Calculate number of required rest stops."""
        if total_hours <= self.REQUIRED_REST_AFTER_HOURS:
            return 0
        return (total_hours - 1) // self.REQUIRED_REST_AFTER_HOURS

    def _calculate_rest_stops(self, route: Route) -> List[TimelineEvent]:
        """Calculate rest stop timeline events."""
        timeline = []

        # Start event
        timeline.append(TimelineEvent(
            type="start",
            time=route.pickup_time - timedelta(hours=route.empty_driving.duration_hours),
            planned_time=route.pickup_time - timedelta(hours=route.empty_driving.duration_hours),
            location=route.origin,
            duration_minutes=0,
            description="Start of route",
            is_required=True
        ))
        
        # Pickup event with loading duration
        timeline.append(TimelineEvent(
            type="pickup",
            time=route.pickup_time,
            planned_time=route.pickup_time,
            location=route.origin,
            duration_minutes=30,  # 30 minutes for loading
            description="Loading cargo",
            is_required=True
        ))
        
        # Calculate rest stops
        current_time = route.pickup_time + timedelta(minutes=30)  # After loading
        remaining_drive_time = route.main_route.duration_hours
        
        while remaining_drive_time > self.REQUIRED_REST_AFTER_HOURS:
            # Add rest stop at calculated location
            rest_time = current_time + timedelta(hours=self.REQUIRED_REST_AFTER_HOURS)
            progress = (self.REQUIRED_REST_AFTER_HOURS * len(timeline)) / route.main_route.duration_hours
            rest_location = Location(
                latitude=route.origin.latitude + (route.destination.latitude - route.origin.latitude) * progress,
                longitude=route.origin.longitude + (route.destination.longitude - route.origin.longitude) * progress,
                address=f"Rest Area {len(timeline)}"
            )
            
            timeline.append(TimelineEvent(
                type="rest",
                time=rest_time,
                planned_time=rest_time,
                location=rest_location,
                duration_minutes=int(self.MIN_REST_DURATION_HOURS * 60),
                description="Required rest period",
                is_required=False
            ))
            
            current_time = rest_time + timedelta(hours=self.MIN_REST_DURATION_HOURS)
            remaining_drive_time -= self.REQUIRED_REST_AFTER_HOURS
        
        # Delivery event with unloading duration
        delivery_start_time = route.delivery_time - timedelta(minutes=30)  # Account for unloading time
        timeline.append(TimelineEvent(
            type="delivery",
            time=delivery_start_time,
            planned_time=delivery_start_time,
            location=route.destination,
            duration_minutes=30,  # 30 minutes for unloading
            description="Unloading cargo",
            is_required=True
        ))
        
        # End event
        timeline.append(TimelineEvent(
            type="end",
            time=route.delivery_time,
            planned_time=route.delivery_time,
            location=route.destination,
            duration_minutes=0,
            description="End of route",
            is_required=True
        ))
        
        return timeline

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
            pickup_time: Pickup time
            delivery_time: Delivery time
            cargo: Optional cargo details
            transport_type: Optional transport type

        Returns:
            Route object with calculated details

        Raises:
            RouteValidationException: If timeline constraints are violated
        """
        self.logger.info(
            "calculating_route",
            origin=origin.address,
            destination=destination.address
        )

        # Create route object
        route = Route(
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            cargo=cargo,
            transport_type=transport_type
        )

        try:
            # Calculate empty driving and main route segments
            route.empty_driving = self._calculate_empty_driving(origin, destination)
            route.main_route = self._calculate_main_route(origin, destination)
            route.total_duration_hours = route.empty_driving.duration_hours + route.main_route.duration_hours

            # Validate timeline
            validation_errors = self.validate_route_timeline(route)
            if validation_errors:
                raise RouteValidationException(validation_errors)

            # Calculate rest stops if needed
            route.timeline_events = self._calculate_rest_stops(route)
            route.has_rest_stops = True
            route.rest_stops_count = self._calculate_required_rest_stops(route.total_duration_hours)
            route.total_rest_duration = route.rest_stops_count * self.MIN_REST_DURATION_HOURS

            # Calculate costs
            cost_calculation = self.cost_calculation_service.calculate_route_cost(route)
            route.total_cost = cost_calculation["total_cost"]
            route.currency = cost_calculation["currency"]
            route.cost_breakdown = cost_calculation["cost_breakdown"]
            route.optimization_insights = cost_calculation["optimization_insights"]
            route.last_calculated = datetime.utcnow()

            # Save route to database
            self.repository.create(route)

            # Track metrics
            self.metrics_service.counter(
                "route.calculation.success",
                labels={
                    "has_cargo": str(bool(cargo)),
                    "has_transport_type": str(bool(transport_type)),
                    "has_rest_stops": str(route.has_rest_stops)
                }
            )
            
            return route

        except Exception as e:
            self.logger.error(
                "route_calculation_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            raise

    def _calculate_empty_driving(self, origin: Location, destination: Location) -> EmptyDriving:
        """Calculate empty driving segment."""
        return EmptyDriving(
            distance_km=200.0,  # Example value - should be replaced with actual calculation
            duration_hours=4.0,  # Example value - should be replaced with actual calculation
            base_cost=75.0,  # Example value - should be calculated based on cost settings
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
            distance_km=700.0,  # Example value - should be replaced with actual calculation
            duration_hours=9.0,  # Example value - should be replaced with actual calculation
            base_cost=1050.0,  # Example value - should be calculated based on cost settings
            country_segments=[
                CountrySegment(
                    country="Germany",
                    distance_km=300.0
                ),
                CountrySegment(
                    country="France",
                    distance_km=400.0
                )
            ]
        )
