from flask import request, jsonify
from flask_restful import Resource
import structlog
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from time import time as get_time

from ...domain.services.route_service import RouteService
from ...domain.services.cost_calculation_service import CostCalculationService
from ...domain.services.cost_optimization_service import CostOptimizationService
from ...domain.validators.cost_setting_validator import CostSettingValidator
from ...infrastructure.database.repositories.route_repository import RouteRepository
from ...infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from ...infrastructure.database.session import SessionLocal
from ...infrastructure.monitoring.metrics_service import MetricsService
from ...domain.entities import Location, Cargo, TransportType, Capacity, Route
from ...domain.exceptions import RouteValidationException

logger = structlog.get_logger(__name__)

class RouteEndpoint(Resource):
    def __init__(self, repository: Optional[RouteRepository] = None, metrics_service: Optional[MetricsService] = None, 
                 cost_settings_repository: Optional[CostSettingsRepository] = None, 
                 cost_calculation_service: Optional[CostCalculationService] = None,
                 cost_optimization_service: Optional[CostOptimizationService] = None):
        """Initialize the RouteEndpoint with optional dependencies."""
        super().__init__()  # Add this back - it's needed for Flask-RESTful
        
        # Initialize repositories
        if repository is None:
            self.repository = RouteRepository(SessionLocal())
        else:
            self.repository = repository
            
        if cost_settings_repository is None:
            self.cost_settings_repository = CostSettingsRepository(SessionLocal())
        else:
            self.cost_settings_repository = cost_settings_repository
            
        # Initialize services
        self.metrics_service = metrics_service or MetricsService()
        self.cost_optimization_service = cost_optimization_service or CostOptimizationService(metrics_service=self.metrics_service)
        self.cost_calculation_service = cost_calculation_service or CostCalculationService(
            cost_settings_repository=self.cost_settings_repository,
            metrics_service=self.metrics_service,
            cost_optimization_service=self.cost_optimization_service
        )
        
        # Initialize validators
        self.cost_validator = CostSettingValidator()
        
        # Initialize route service
        self.route_service = RouteService(
            repository=self.repository,
            cost_settings_repository=self.cost_settings_repository,
            cost_calculation_service=self.cost_calculation_service,
            cost_validator=self.cost_validator,
            metrics_service=self.metrics_service
        )
        
        self.logger = logger.bind(endpoint="route")
        self.logger.info("route_endpoint_initialized")

    def post(self):
        """Calculate a route."""
        self.logger.debug("Starting post method")
        
        try:
            self.logger.debug("Getting JSON data")
            data = request.get_json()
            if not data:
                self.logger.error("no_request_data")
                return {"error": "No request data provided"}, 400

            self.logger.info("received_route_request", data=data)

            # Parse origin and destination addresses
            self.logger.debug("Parsing locations")
            origin = Location(
                address=data["origin"]["address"],
                latitude=data["origin"]["latitude"],
                longitude=data["origin"]["longitude"]
            )
            destination = Location(
                address=data["destination"]["address"],
                latitude=data["destination"]["latitude"],
                longitude=data["destination"]["longitude"]
            )

            # Parse dates
            self.logger.debug("Parsing dates")
            try:
                # Parse dates and make them timezone-aware (using UTC)
                pickup_time = datetime.fromisoformat(data["pickup_time"].replace('Z', '+00:00'))
                if not pickup_time.tzinfo:
                    pickup_time = pickup_time.replace(tzinfo=timezone.utc)
                
                delivery_time = datetime.fromisoformat(data["delivery_time"].replace('Z', '+00:00'))
                if not delivery_time.tzinfo:
                    delivery_time = delivery_time.replace(tzinfo=timezone.utc)
                
                # Basic validation before proceeding
                if delivery_time <= pickup_time:
                    return {"error": "Delivery time must be after pickup time"}, 400
                
                # Check if pickup time is within loading window (6 AM - 10 PM)
                pickup_hour = pickup_time.hour
                if pickup_hour < 6 or pickup_hour >= 22:
                    return {
                        "error": "Invalid pickup time",
                        "details": "Pickup must be scheduled between 6 AM and 10 PM"
                    }, 400
                
            except ValueError as e:
                return {"error": f"Invalid date format: {str(e)}"}, 400

            # Parse cargo if provided
            self.logger.debug("Parsing cargo")
            cargo = None
            if "cargo" in data:
                cargo = Cargo(
                    type=data["cargo"]["type"],
                    weight=data["cargo"]["weight"],
                    value=data["cargo"]["value"],
                    special_requirements=data["cargo"]["special_requirements"]
                )

            # Create route
            self.logger.debug("Creating route")
            try:
                route = self.route_service.calculate_route(
                    origin=origin,
                    destination=destination,
                    pickup_time=pickup_time,
                    delivery_time=delivery_time,
                    cargo=cargo
                )
                self.logger.info("route_calculated", route_id=str(route.id))
                return route.to_dict(), 200

            except RouteValidationException as e:
                self.logger.error("route_validation_failed", errors=str(e.errors))
                return {"error": "Route validation failed", "details": [str(err) for err in e.errors]}, 400

        except Exception as e:
            self.logger.error(
                "route_calculation_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            return {"error": str(e)}, 500
