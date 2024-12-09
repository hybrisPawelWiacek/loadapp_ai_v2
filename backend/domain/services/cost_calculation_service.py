from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import structlog
from dataclasses import dataclass

from ..entities import Route, CostSetting, Cargo
from backend.infrastructure.monitoring.performance_metrics import measure_service_operation_time

@dataclass
class ValidationError:
    field: str
    message: str

class CostCalculationError(Exception):
    """Base exception for cost calculation errors."""
    pass

class RouteValidationError(CostCalculationError):
    """Exception raised for invalid route data."""
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        error_messages = [f"{e.field}: {e.message}" for e in errors]
        super().__init__(f"Route validation failed: {'; '.join(error_messages)}")

class CostCalculationService:
    """Service for calculating costs based on route data."""

    def __init__(self):
        """Initialize the cost calculation service."""
        self.logger = structlog.get_logger(__name__)
        self.logger.info("Initializing CostCalculationService")
        self._load_base_rates()

    def _load_base_rates(self):
        """Load base rates for cost calculations."""
        self._base_rates = {
            "fuel": 1.5,  # EUR per km
            "driver": 35.0,  # EUR per hour
            "toll": 0.2,  # EUR per km
            "maintenance": 0.3,  # EUR per km
            "insurance": 50.0,  # EUR per day
            "overhead": 100.0,  # EUR per day
            "adr_surcharge": 0.5,  # EUR per km for dangerous goods
            "refrigeration": 0.4,  # EUR per km for temperature control
            "high_value": 0.003,  # 0.3% of cargo value per day
        }
        self.logger.info("base_rates_loaded", base_rates=self._base_rates)

    def _validate_route(self, route: Route) -> List[ValidationError]:
        """Validate route data for required attributes and valid values."""
        errors = []
        
        # Check required attributes
        if not hasattr(route, 'id') or not route.id:
            errors.append(ValidationError("id", "Route ID is required"))
        
        # Validate empty driving data
        if not hasattr(route, 'empty_driving'):
            errors.append(ValidationError("empty_driving", "Empty driving data is required"))
        elif route.empty_driving:
            if not hasattr(route.empty_driving, 'distance_km'):
                errors.append(ValidationError("empty_driving.distance_km", "Empty driving distance is required"))
            elif route.empty_driving.distance_km < 0:
                errors.append(ValidationError("empty_driving.distance_km", "Distance cannot be negative"))
            
            if not hasattr(route.empty_driving, 'duration_hours'):
                errors.append(ValidationError("empty_driving.duration_hours", "Empty driving duration is required"))
            elif route.empty_driving.duration_hours < 0:
                errors.append(ValidationError("empty_driving.duration_hours", "Duration cannot be negative"))
        
        # Validate main route data
        if not hasattr(route, 'main_route'):
            errors.append(ValidationError("main_route", "Main route data is required"))
        elif route.main_route:
            if not hasattr(route.main_route, 'distance_km'):
                errors.append(ValidationError("main_route.distance_km", "Main route distance is required"))
            elif route.main_route.distance_km < 0:
                errors.append(ValidationError("main_route.distance_km", "Distance cannot be negative"))
            
            if not hasattr(route.main_route, 'country_segments'):
                errors.append(ValidationError("main_route.country_segments", "Country segments are required"))
        
        return errors

    def _calculate_empty_driving_costs(self, route: Route) -> Dict:
        """Calculate costs for empty driving segment."""
        try:
            empty_distance = route.empty_driving.distance_km
            empty_duration = route.empty_driving.duration_hours

            # Data sanity checks
            if empty_distance > 1000:
                self.logger.warning("unusually_long_empty_driving",
                                route_id=str(route.id),
                                distance=empty_distance)
            
            if empty_duration > 24:
                self.logger.warning("unusually_long_empty_duration",
                                route_id=str(route.id),
                                duration=empty_duration)

            costs = {
                "fuel": empty_distance * self._base_rates["fuel"],
                "driver": empty_duration * self._base_rates["driver"],
                "toll": empty_distance * self._base_rates["toll"],
                "maintenance": empty_distance * self._base_rates["maintenance"]
            }

            self.logger.info("empty_driving_costs_calculated", 
                           route_id=str(route.id),
                           costs=costs)
            return costs

        except Exception as e:
            self.logger.error("empty_driving_calculation_failed",
                            error=str(e),
                            route_id=str(route.id))
            raise CostCalculationError(f"Failed to calculate empty driving costs: {str(e)}")

    def _calculate_main_route_costs(self, route: Route) -> Dict:
        """Calculate costs for main route segment."""
        try:
            main_distance = route.main_route.distance_km
            main_duration = sum(segment.duration_hours for segment in route.main_route.country_segments)

            # Data sanity checks
            if main_distance > 5000:
                self.logger.warning("unusually_long_main_route",
                                route_id=str(route.id),
                                distance=main_distance)
            
            if main_duration > 100:
                self.logger.warning("unusually_long_route_duration",
                                route_id=str(route.id),
                                duration=main_duration)

            costs = {
                "fuel": main_distance * self._base_rates["fuel"],
                "driver": main_duration * self._base_rates["driver"],
                "toll": main_distance * self._base_rates["toll"],
                "maintenance": main_distance * self._base_rates["maintenance"]
            }

            # Add country-specific costs
            country_costs = {}
            for segment in route.main_route.country_segments:
                if not hasattr(segment, 'distance_km') or segment.distance_km < 0:
                    self.logger.warning("invalid_country_segment",
                                    route_id=str(route.id),
                                    country=segment.country)
                    continue
                    
                country_costs[segment.country] = segment.distance_km * self._base_rates["toll"]

            costs["country_specific"] = country_costs

            self.logger.info("main_route_costs_calculated",
                           route_id=str(route.id),
                           costs=costs)
            return costs

        except Exception as e:
            self.logger.error("main_route_calculation_failed",
                            error=str(e),
                            route_id=str(route.id))
            raise CostCalculationError(f"Failed to calculate main route costs: {str(e)}")

    def _calculate_cargo_costs(self, route: Route) -> Dict:
        """Calculate cargo-specific costs."""
        try:
            costs = {}
            if route.cargo:
                main_distance = route.main_route.distance_km
                total_duration_days = route.total_duration_hours / 24.0

                # Data sanity checks
                if hasattr(route.cargo, 'value') and route.cargo.value > 1000000:
                    self.logger.warning("unusually_high_cargo_value",
                                    route_id=str(route.id),
                                    cargo_value=route.cargo.value)

                # ADR surcharge for dangerous goods
                if hasattr(route.cargo, 'special_requirements') and "ADR" in route.cargo.special_requirements:
                    costs["adr_surcharge"] = main_distance * self._base_rates["adr_surcharge"]

                # Temperature control costs
                if hasattr(route.cargo, 'special_requirements') and "Temperature controlled" in route.cargo.special_requirements:
                    costs["refrigeration"] = main_distance * self._base_rates["refrigeration"]

                # High value cargo insurance
                if hasattr(route.cargo, 'value') and route.cargo.value > 100000:
                    costs["high_value_insurance"] = (
                        route.cargo.value * self._base_rates["high_value"] * total_duration_days
                    )

            self.logger.info("cargo_costs_calculated",
                           route_id=str(route.id),
                           costs=costs)
            return costs

        except Exception as e:
            self.logger.error("cargo_cost_calculation_failed",
                            error=str(e),
                            route_id=str(route.id))
            raise CostCalculationError(f"Failed to calculate cargo costs: {str(e)}")

    def _calculate_fixed_costs(self, route: Route) -> Dict:
        """Calculate fixed costs based on route duration."""
        try:
            # Round up to full days
            total_days = (route.total_duration_hours + 23) // 24

            # Data sanity check
            if total_days > 14:  # Two weeks
                self.logger.warning("unusually_long_route_duration",
                                route_id=str(route.id),
                                total_days=total_days)

            costs = {
                "insurance": total_days * self._base_rates["insurance"],
                "overhead": total_days * self._base_rates["overhead"]
            }

            self.logger.info("fixed_costs_calculated",
                           route_id=str(route.id),
                           costs=costs)
            return costs

        except Exception as e:
            self.logger.error("fixed_cost_calculation_failed",
                            error=str(e),
                            route_id=str(route.id))
            raise CostCalculationError(f"Failed to calculate fixed costs: {str(e)}")

    def _aggregate_costs(self, empty_driving: Dict, main_route: Dict, 
                        cargo: Dict, fixed: Dict) -> Dict:
        """Aggregate all cost components and calculate total."""
        try:
            # Initialize total cost
            total_cost = 0.0

            # Create cost breakdown structure
            breakdown = {
                "empty_driving": empty_driving,
                "main_route": main_route,
                "cargo_specific": cargo,
                "fixed_costs": fixed
            }

            # Calculate total
            total_cost += sum(empty_driving.values())
            total_cost += sum(v for k, v in main_route.items() 
                            if k != "country_specific")
            total_cost += sum(main_route.get("country_specific", {}).values())
            total_cost += sum(cargo.values())
            total_cost += sum(fixed.values())

            # Sanity check on total cost
            if total_cost > 50000:  # Arbitrary threshold for demonstration
                self.logger.warning("unusually_high_total_cost",
                                total_cost=total_cost)

            return {
                "total_cost": round(total_cost, 2),
                "currency": "EUR",
                "breakdown": breakdown
            }

        except Exception as e:
            self.logger.error("cost_aggregation_failed",
                            error=str(e))
            raise CostCalculationError(f"Failed to aggregate costs: {str(e)}")

    @measure_service_operation_time(service="CostCalculationService", operation="calculate_costs")
    def calculate_total_cost(self, route: Route) -> Dict:
        """Calculate the total cost for a route with input validation."""
        try:
            # Validate route data
            validation_errors = self._validate_route(route)
            if validation_errors:
                raise RouteValidationError(validation_errors)

            self.logger.info("starting_cost_calculation", route_id=str(route.id))

            # Calculate all cost components
            empty_driving_costs = self._calculate_empty_driving_costs(route)
            main_route_costs = self._calculate_main_route_costs(route)
            cargo_costs = self._calculate_cargo_costs(route)
            fixed_costs = self._calculate_fixed_costs(route)

            # Aggregate all costs
            total_costs = self._aggregate_costs(
                empty_driving_costs,
                main_route_costs,
                cargo_costs,
                fixed_costs
            )

            self.logger.info("cost_calculation_completed",
                           route_id=str(route.id),
                           total_cost=total_costs["total_cost"])

            return total_costs

        except RouteValidationError as e:
            self.logger.error("route_validation_failed",
                            route_id=str(getattr(route, 'id', 'unknown')),
                            errors=str(e))
            raise

        except CostCalculationError as e:
            self.logger.error("cost_calculation_failed",
                            route_id=str(getattr(route, 'id', 'unknown')),
                            error=str(e))
            raise

        except Exception as e:
            self.logger.error("unexpected_error",
                            route_id=str(getattr(route, 'id', 'unknown')),
                            error=str(e))
            raise CostCalculationError(f"Unexpected error during cost calculation: {str(e)}")

    def get_cost_items(self) -> List[CostSetting]:
        """Get list of cost items with their current settings"""
        try:
            cost_items = [
                CostSetting(
                    id=uuid4(),
                    type="fuel",
                    category="variable",
                    base_value=self._base_rates["fuel"],
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True,
                    description="Fuel cost per kilometer"
                ),
                # ... other cost items
            ]
            
            self.logger.info("cost_items_retrieved", count=len(cost_items))
            return cost_items
            
        except Exception as e:
            self.logger.error("error_retrieving_cost_items", error=str(e))
            raise CostCalculationError(f"Failed to retrieve cost items: {str(e)}")
    
    def _get_cost_description(self, cost_type: str) -> str:
        """Get human-readable description for cost types"""
        self.logger.info("getting_cost_description", cost_type=cost_type)
