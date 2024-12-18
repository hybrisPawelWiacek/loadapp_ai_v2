from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4
import structlog
from dataclasses import dataclass

from ..entities import Route, CostItem, Cargo, CostSetting
from backend.infrastructure.monitoring.performance_metrics import measure_service_operation_time
from backend.infrastructure.database.repositories.cost_setting_repository import CostSettingsRepository
from backend.infrastructure.monitoring.metrics_service import MetricsService
from backend.domain.services.cost_optimization_service import CostOptimizationService, CostPattern

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
    """Service for calculating costs based on route data and cost settings."""

    def __init__(
            self,
            cost_settings_repository: CostSettingsRepository,
            metrics_service: MetricsService,
            cost_optimization_service: CostOptimizationService
        ):
        """Initialize the cost calculation service with required dependencies."""
        self.logger = structlog.get_logger(__name__)
        self.cost_settings_repository = cost_settings_repository
        self.metrics_service = metrics_service
        self.cost_optimization_service = cost_optimization_service

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

    @measure_service_operation_time(service="CostCalculationService", operation="calculate_route_cost")
    def calculate_route_cost(self, route: Route, settings: Dict[str, Any] = None) -> Dict:
        """
        Calculate the total cost for a given route using enabled cost settings.
        
        Args:
            route: Route object containing all necessary route information
            settings: Optional dictionary of cost settings to use. If not provided,
                     will use enabled settings from repository.
            
        Returns:
            Dictionary containing:
            - total_cost: Total cost of the route
            - currency: Currency used for calculations
            - cost_breakdown: Detailed breakdown of costs (base_cost, fuel_cost, etc.)
            - optimization_insights: Optional insights for cost optimization
            
        Raises:
            RouteValidationError: If route data is invalid
            CostCalculationError: If calculation fails
        """
        try:
            # Log input data types
            self.logger.debug(
                "starting_cost_calculation",
                route_id=route.id,
                route_id_type=type(route.id).__name__,
                settings_count=len(settings) if settings else 0,
                settings_types={k: type(v).__name__ for k, v in (settings or {}).items()}
            )
            
            # Validate route data
            validation_errors = self._validate_route(route)
            if validation_errors:
                raise RouteValidationError(validation_errors)
            
            # Get cost settings
            cost_settings = []
            if settings:
                # Log settings conversion
                self.logger.debug(
                    "converting_settings",
                    settings_keys=list(settings.keys()),
                    settings_values_types={k: type(v).__name__ for k, v in settings.items()}
                )
                
                # Convert settings dict to CostSetting objects
                for setting_type, setting_value in settings.items():
                    setting_id = uuid4()
                    self.logger.debug(
                        "creating_cost_setting",
                        setting_type=setting_type,
                        setting_id=setting_id,
                        setting_id_type=type(setting_id).__name__,
                        value_type=type(setting_value).__name__
                    )
                    
                    try:
                        cost_settings.append(CostSetting(
                            id=setting_id,
                            name=f"{setting_type.title()} Cost",
                            type=setting_type,
                            category="variable",
                            base_value=float(setting_value),
                            description=f"Auto-generated {setting_type} cost setting"
                        ))
                    except Exception as e:
                        self.logger.error(
                            "cost_setting_creation_failed",
                            setting_type=setting_type,
                            setting_id=setting_id,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise
            else:
                # Get enabled cost settings from repository
                self.logger.debug("fetching_enabled_cost_settings")
                cost_settings = self.cost_settings_repository.get_enabled_cost_settings()
                if not cost_settings:
                    raise CostCalculationError("No enabled cost settings found")
                
                self.logger.debug(
                    "fetched_cost_settings",
                    settings_count=len(cost_settings),
                    settings_ids=[str(s.id) for s in cost_settings],
                    settings_types=[s.type for s in cost_settings]
                )
            
            # Perform cost calculation
            self.logger.debug(
                "performing_calculation",
                route_id=route.id,
                cost_settings_count=len(cost_settings)
            )
            cost_breakdown = self._perform_calculation(route, cost_settings)
            
            # Get historical costs for pattern analysis
            historical_costs = self._get_historical_costs(route)
            
            # Analyze cost patterns and get optimization suggestions
            patterns = self.cost_optimization_service.analyze_cost_patterns(
                route=route,
                historical_costs=historical_costs,
                time_window_days=90
            )
            
            # Convert patterns to dictionary format
            optimization_insights = {
                "patterns": [self._pattern_to_dict(pattern) for pattern in patterns],
                "suggestions": []  # We'll add suggestions later when implemented
            }
            
            # Return result in a format that works for both RouteService and OfferService
            return {
                "total_cost": cost_breakdown["total"],
                "currency": route.currency,
                "cost_breakdown": cost_breakdown,
                "optimization_insights": optimization_insights
            }
            
        except RouteValidationError as e:
            self.metrics_service.counter(
                "cost_calculation.validation_errors",
                labels={"route_id": str(route.id)}
            )
            self.logger.error("route_validation_failed", 
                            route_id=str(route.id),
                            errors=str(e))
            raise
            
        except Exception as e:
            self.logger.error("cost_calculation_failed",
                            route_id=str(route.id),
                            error=str(e))
            raise CostCalculationError(f"Failed to calculate route cost: {str(e)}")

    def _get_historical_costs(self, route: Route) -> List[Dict]:
        """Get historical costs for pattern analysis."""
        try:
            # Mock historical data
            return [
                {
                    "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "total_cost": 1000 + (i * 10),  # Mock cost variation
                    "breakdown": {
                        "fuel": 400 + (i * 5),
                        "maintenance": 200 + (i * 2),
                        "time": 300 + (i * 3)
                    }
                }
                for i in range(90)  # 90 days of history
            ]
        except Exception as e:
            self.logger.error("failed_to_get_historical_costs",
                            route_id=str(route.id),
                            error=str(e))
            return []

    def _pattern_to_dict(self, pattern: CostPattern) -> Dict:
        """Convert a CostPattern to a dictionary for API response."""
        return {
            "type": pattern.pattern_type,
            "description": pattern.description,
            "impact_score": pattern.impact_score,
            "affected_components": pattern.affected_components,
            "confidence": pattern.confidence,
            "recommendations": pattern.recommendations
        }

    def _suggestion_to_dict(self, suggestion) -> Dict:
        """Convert an OptimizationSuggestion to a dictionary for API response."""
        return {
            "id": str(suggestion.suggestion_id),
            "title": suggestion.title,
            "description": suggestion.description,
            "estimated_savings": suggestion.estimated_savings,
            "implementation_complexity": suggestion.implementation_complexity,
            "priority": suggestion.priority,
            "affected_settings": suggestion.affected_settings,
            "prerequisites": suggestion.prerequisites,
            "risks": suggestion.risks
        }

    def _perform_calculation(self, route: Route, cost_settings: List[CostSetting]) -> Dict:
        """
        Perform the actual cost calculation using the provided cost settings.
        """
        try:
            self.logger.debug(
                "starting_perform_calculation",
                route_id=route.id,
                cost_settings_ids=[str(s.id) for s in cost_settings],
                cost_settings_types=[s.type for s in cost_settings]
            )
            
            # Initialize cost breakdown
            cost_breakdown = {
                "base_costs": {},
                "variable_costs": {},
                "cargo_specific_costs": {},
                "total": 0.0
            }
            
            # Calculate costs for each setting
            for setting in cost_settings:
                self.logger.debug(
                    "calculating_setting_cost",
                    setting_id=setting.id,
                    setting_type=setting.type,
                    setting_category=setting.category
                )
                
                try:
                    if setting.category == "variable":
                        cost = self._calculate_variable_cost(route, setting)
                        cost_breakdown["variable_costs"][setting.type] = cost
                    elif setting.category == "cargo" and route.cargo:
                        cost = self._calculate_cargo_costs(route.cargo, [setting])
                        cost_breakdown["cargo_specific_costs"][setting.type] = cost
                    else:
                        cost = setting.base_value
                        cost_breakdown["base_costs"][setting.type] = cost
                        
                    self.logger.debug(
                        "calculated_setting_cost",
                        setting_id=setting.id,
                        setting_type=setting.type,
                        cost=cost
                    )
                        
                except Exception as e:
                    self.logger.error(
                        "setting_calculation_failed",
                        setting_id=setting.id,
                        setting_type=setting.type,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    raise
            
            # Calculate total cost
            cost_breakdown["total"] = sum(
                cost_breakdown["base_costs"].values()
            ) + sum(
                cost_breakdown["variable_costs"].values()
            ) + sum(
                [sum(costs.values()) for costs in cost_breakdown["cargo_specific_costs"].values()]
            )
            
            self.logger.debug(
                "total_cost_calculated",
                route_id=route.id,
                total_cost=cost_breakdown["total"]
            )
            
            return cost_breakdown
            
        except Exception as e:
            self.logger.error("calculation_step_failed",
                            route_id=str(route.id),
                            error=str(e))
            raise

    def _calculate_variable_cost(self, route: Route, setting: CostSetting) -> float:
        """Calculate variable cost based on route properties."""
        base_cost = setting.apply_multiplier()
        
        # Calculate total distance including empty driving
        total_distance = route.main_route.distance_km
        if route.empty_driving:
            total_distance += route.empty_driving.distance_km
            
        # Calculate total duration in hours
        total_duration = route.main_route.duration_hours
        if route.empty_driving:
            total_duration += route.empty_driving.duration_hours
        
        # Apply route-specific multipliers based on setting type
        cost = 0.0
        if setting.type == "fuel":
            # Fuel cost is based on distance
            cost = base_cost * total_distance
        elif setting.type == "driver":
            # Driver cost is based on duration
            cost = base_cost * total_duration
        elif setting.type == "maintenance":
            # Maintenance cost considers both distance and time
            distance_cost = base_cost * total_distance * 0.7  # 70% distance-based
            time_cost = base_cost * total_duration * 0.3     # 30% time-based
            cost = distance_cost + time_cost
        elif setting.type == "toll":
            # Toll cost is purely distance-based
            cost = base_cost * total_distance
        else:
            # Default to time-based cost for unknown types
            cost = base_cost * total_duration
            
        self.logger.debug(
            "variable_cost_calculated",
            route_id=str(route.id),
            setting_type=setting.type,
            base_cost=base_cost,
            total_distance=total_distance,
            total_duration=total_duration,
            final_cost=cost
        )
        
        return cost

    def _calculate_cargo_costs(
        self, cargo: Cargo, settings: List[CostSetting]
    ) -> Dict[str, float]:
        """Calculate costs specific to a cargo item."""
        cargo_costs = {}
        
        for setting in settings:
            base_cost = setting.apply_multiplier()
            
            if setting.type == "weight":
                cargo_costs[setting.type] = base_cost * cargo.weight
            elif setting.type == "volume":
                cargo_costs[setting.type] = base_cost * cargo.volume
            elif setting.type == "handling":
                cargo_costs[setting.type] = base_cost * (
                    1 + cargo.handling_factor
                )
            else:
                cargo_costs[setting.type] = base_cost
        
        return cargo_costs

    def get_cost_items(self) -> List[CostItem]:
        """Get list of cost items with their current settings"""
        try:
            cost_items = [
                CostItem(
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
