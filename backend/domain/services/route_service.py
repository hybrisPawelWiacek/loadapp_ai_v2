from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import structlog

from ...domain.entities.route import Route, EmptyDriving, MainRoute, CountrySegment, TimelineEvent
from ...domain.entities.cost_setting import CostSetting
from ...domain.entities.location import Location
from ...domain.entities.cargo import Cargo, TransportType, Capacity
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
    """Service for managing route operations."""

    def __init__(
        self,
        repository,
        cost_settings_repository,
        cost_calculation_service,
        cost_validator,
        metrics_service
    ):
        """Initialize the route service.
        
        Args:
            repository: Repository for route operations
            cost_settings_repository: Repository for cost settings
            cost_calculation_service: Service for cost calculations
            cost_validator: Validator for cost settings
            metrics_service: Service for metrics tracking
        """
        self.repository = repository
        self.cost_settings_repository = cost_settings_repository
        self.cost_calculation_service = cost_calculation_service
        self.cost_validator = cost_validator
        self.metrics_service = metrics_service
        self.logger = structlog.get_logger(__name__)

    def create_route(self, route_data: dict, cost_settings: Optional[List[dict]] = None) -> Route:
        """Create a new route with the given data and cost settings.
        
        Args:
            route_data: Dictionary containing route data
            cost_settings: Optional list of cost settings to use
            
        Returns:
            Created Route entity
            
        Raises:
            ValidationError: If route data or cost settings are invalid
            BusinessRuleError: If business rules are violated
        """
        try:
            self.logger.info(
                "creating_route",
                route_id=route_data.get('id'),
                route_id_type=type(route_data.get('id')),
                cost_settings_count=len(cost_settings) if cost_settings else 0,
                cost_settings_ids=[cs.get('id') for cs in cost_settings] if cost_settings else [],
                cost_settings_types=[cs.get('type') for cs in cost_settings] if cost_settings else []
            )

            # Validate cost settings if provided
            if cost_settings:
                validation_errors = self.validate_route_cost_settings(cost_settings)
                if validation_errors:
                    self.logger.error(
                        "cost_settings_validation_failed",
                        errors=validation_errors
                    )
                    raise ValidationError("Invalid cost settings", validation_errors)

            # Convert dictionaries to entity objects
            self.logger.debug("Converting route to dictionary")
            
            # Create Location objects
            origin = Location(**route_data['origin']) if isinstance(route_data['origin'], dict) else route_data['origin']
            destination = Location(**route_data['destination']) if isinstance(route_data['destination'], dict) else route_data['destination']
            
            # Create TransportType object if provided
            transport_type = None
            if route_data.get('transport_type'):
                transport_type = TransportType(**route_data['transport_type']) if isinstance(route_data['transport_type'], dict) else route_data['transport_type']
            
            # Create Cargo object if provided
            cargo = None
            if route_data.get('cargo'):
                cargo = Cargo(**route_data['cargo']) if isinstance(route_data['cargo'], dict) else route_data['cargo']
            
            # Create EmptyDriving object
            empty_driving = EmptyDriving(**route_data['empty_driving']) if isinstance(route_data['empty_driving'], dict) else route_data['empty_driving']
            
            # Create MainRoute object
            main_route = MainRoute(**route_data['main_route']) if isinstance(route_data['main_route'], dict) else route_data['main_route']
            
            # Create TimelineEvent objects
            timeline_events = []
            for event_data in route_data.get('timeline_events', []):
                if isinstance(event_data, dict):
                    # Convert Location in event if it's a dict
                    if isinstance(event_data.get('location'), dict):
                        event_data['location'] = Location(**event_data['location'])
                    timeline_events.append(TimelineEvent(**event_data))
                else:
                    timeline_events.append(event_data)

            # Create Route object
            route = Route(
                origin=origin,
                destination=destination,
                pickup_time=route_data['pickup_time'],
                delivery_time=route_data['delivery_time'],
                transport_type=transport_type,
                cargo=cargo,
                empty_driving=empty_driving,
                main_route=main_route,
                timeline_events=timeline_events,
                total_duration_hours=route_data.get('total_duration_hours', 0.0),
                is_feasible=route_data.get('is_feasible', True),
                duration_validation=route_data.get('duration_validation', True)
            )

            # Save route
            saved_route = self.repository.create(route)
            
            self.logger.info(
                "route_created_successfully",
                route_id=saved_route.id
            )
            
            return saved_route

        except Exception as e:
            self.logger.error(
                "route_creation_failed",
                error=str(e),
                error_type=type(e).__name__,
                route_id=route_data.get('id'),
                traceback=True
            )
            raise

    def validate_route_cost_settings(self, cost_settings: List[dict]) -> List[str]:
        """Validate cost settings for a route.
        
        Args:
            cost_settings: List of cost settings to validate
            
        Returns:
            List of validation error messages
        """
        try:
            # Get enabled cost settings from repository
            enabled_settings = self.cost_settings_repository.get_enabled_cost_settings()
            
            validation_errors = []
            
            # Validate each cost setting
            for setting in cost_settings:
                if not any(es.id == setting['id'] for es in enabled_settings):
                    validation_errors.append(f"Cost setting {setting['id']} is not enabled")
                    
            return validation_errors
            
        except Exception as e:
            self.logger.error(
                "cost_settings_validation_failed",
                error=str(e)
            )
            raise

    def calculate_route(
            self,
            origin: Location,
            destination: Location,
            pickup_time: datetime,
            delivery_time: datetime,
            cargo: Optional[Cargo] = None,
            transport_type: Optional[TransportType] = None
        ) -> Route:
            """Calculate a route between two locations.
            
            Args:
                origin: Origin location
                destination: Destination location
                pickup_time: Pickup time
                delivery_time: Delivery time
                cargo: Optional cargo details
                transport_type: Optional transport type
                
            Returns:
                Calculated route with all details
                
            Raises:
                ValidationError: If route parameters are invalid
                BusinessRuleError: If business rules are violated
            """
            try:
                self.logger.info(
                    "calculating_route",
                    origin=origin.address,
                    destination=destination.address,
                    pickup_time=pickup_time.isoformat(),
                    delivery_time=delivery_time.isoformat()
                )

                # Create default transport type if not provided
                if transport_type is None:
                    transport_type = TransportType(
                        name="Standard Truck",
                        capacity=Capacity(max_weight=24000, max_volume=80),
                        restrictions=[]
                    )

                # Create cargo object if provided as dict
                if isinstance(cargo, dict):
                    cargo = Cargo(
                        type=cargo.get('type', 'Standard'),
                        weight=float(cargo.get('weight', 0)),
                        value=float(cargo.get('value', 0)),
                        special_requirements=cargo.get('special_requirements', [])
                    )

                # Calculate empty driving segment
                empty_driving = EmptyDriving(
                    distance_km=200.0,  # Example value - should be calculated based on actual distance
                    duration_hours=4.0,  # Example value - should be calculated based on actual duration
                    base_cost=100.0,
                    country_segments=[
                        CountrySegment(
                            country="DE",
                            distance_km=200.0,
                            duration_hours=4.0
                        )
                    ]
                )

                # Calculate main route segment
                main_route = MainRoute(
                    distance_km=1050.0,  # Example value - should be calculated based on actual distance
                    duration_hours=10.5,  # Example value - should be calculated based on actual duration
                    base_cost=150.0,
                    country_segments=[
                        CountrySegment(
                            country="DE",
                            distance_km=500.0,
                            duration_hours=5.0
                        ),
                        CountrySegment(
                            country="FR",
                            distance_km=550.0,
                            duration_hours=5.5
                        )
                    ]
                )

                # Create timeline events
                timeline_events = [
                    TimelineEvent(
                        event_type="pickup",
                        type="pickup",  # For backward compatibility
                        location=origin,
                        time=pickup_time,
                        planned_time=pickup_time,
                        duration_minutes=30,
                        description=f"Pickup at {origin.address}",
                        is_required=True
                    ),
                    TimelineEvent(
                        event_type="delivery",
                        type="delivery",  # For backward compatibility
                        location=destination,
                        time=delivery_time,
                        planned_time=delivery_time,
                        duration_minutes=30,
                        description=f"Delivery at {destination.address}",
                        is_required=True
                    )
                ]

                # Create route data dictionary
                route_data = {
                    'origin': origin.__dict__,
                    'destination': destination.__dict__,
                    'pickup_time': pickup_time,
                    'delivery_time': delivery_time,
                    'transport_type': transport_type.to_dict(),
                    'cargo': cargo.to_dict() if cargo else None,
                    'empty_driving': empty_driving.__dict__,
                    'main_route': main_route.__dict__,
                    'timeline_events': [event.__dict__ for event in timeline_events],
                    'total_duration_hours': empty_driving.duration_hours + main_route.duration_hours,
                    'is_feasible': True,
                    'duration_validation': True
                }

                # Create and save route
                route = self.create_route(route_data)
                
                self.logger.info(
                    "route_calculated_successfully",
                    route_id=route.id
                )
                
                return route

            except Exception as e:
                self.logger.error(
                    "route_calculation_failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
