from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import structlog

from ..entities import Route, CostSetting, Cargo, Cost
from backend.infrastructure.monitoring.performance_metrics import measure_service_operation_time

class CostCalculationService:
    """Service for calculating costs based on route data."""

    def __init__(self):
        """Initialize the cost calculation service."""
        self.logger = structlog.get_logger(__name__)
        self.logger.info("Initializing CostCalculationService")
        # Mock base rates for different cost components
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
        self.logger.info("cost_calculation_service_initialized", base_rates=self._base_rates)

    @measure_service_operation_time(service="CostCalculationService", operation="calculate_costs")
    def calculate_total_cost(self, route: Route) -> Dict:
        """Calculate the total cost for a route."""
        self.logger.info("calculating_total_cost", route_id=str(route.id))
        
        try:
            # Calculate total distance (main route + empty driving)
            total_distance = route.main_route.distance_km + route.empty_driving.distance_km
            self.logger.info("route_distances", 
                           main_route_km=route.main_route.distance_km,
                           empty_driving_km=route.empty_driving.distance_km,
                           total_km=total_distance)
            
            # Calculate total duration in hours
            total_duration = route.total_duration_hours
            self.logger.info("route_duration", total_hours=total_duration)
            
            # For now, return a simple mock cost calculation
            costs = {
                "total_cost": 1000.00,
                "currency": "EUR",
                "breakdown": {
                    "base_cost": 500.00,
                    "distance_cost": total_distance * 0.5,  # €0.50 per km
                    "time_cost": total_duration * 50.00,    # €50 per hour
                    "empty_driving_cost": route.empty_driving.distance_km * 0.3  # €0.30 per km for empty driving
                }
            }
            
            self.logger.info("costs_calculated", costs=costs)
            return costs
            
        except Exception as e:
            self.logger.error("error_calculating_costs", error=str(e))
            raise

    def get_cost_items(self) -> List[CostSetting]:
        """
        Get list of all cost items with their current rates.
        
        Returns:
            List of CostSetting objects
        """
        self.logger.info("getting_cost_items")
        cost_items = []
        
        for cost_type, base_value in self._base_rates.items():
            category = "fixed" if cost_type in ["insurance", "overhead"] else "variable"
            
            cost_items.append(
                CostSetting(
                    id=uuid4(),
                    type=cost_type,
                    category=category,
                    base_value=base_value,
                    description=self._get_cost_description(cost_type),
                    multiplier=1.0,
                    currency="EUR",
                    is_enabled=True
                )
            )
        
        self.logger.info("cost_items_retrieved", count=len(cost_items))
        return cost_items
    
    def _calculate_country_specific_costs(self, route: Route) -> Dict[str, float]:
        """Calculate additional costs specific to each country segment"""
        self.logger.info("calculating_country_specific_costs", route_id=str(route.id))
        country_costs = {}
        
        for segment in route.main_route.country_segments:
            # Mock country-specific cost rates
            country_rates = {
                "Germany": {"toll": 0.25, "permit": 50.0},
                "Poland": {"toll": 0.15, "permit": 30.0},
                "Czech Republic": {"toll": 0.20, "permit": 40.0},
                # Add more countries as needed
            }
            
            if segment.country in country_rates:
                rates = country_rates[segment.country]
                country_key = f"{segment.country.lower()}_costs"
                country_costs[country_key] = (
                    segment.distance_km * rates["toll"] + rates["permit"]
                )
        
        self.logger.info("country_costs_calculated", country_costs=country_costs)
        return country_costs
    
    def _calculate_cargo_specific_costs(
        self, 
        cargo: Cargo, 
        total_distance: float,
        days: int
    ) -> Dict[str, float]:
        """Calculate additional costs specific to cargo type and properties"""
        self.logger.info("calculating_cargo_specific_costs", cargo_id=str(cargo.id))
        cargo_costs = {}
        
        # ADR surcharge for dangerous goods
        if "ADR" in (cargo.special_requirements or []):
            cargo_costs["adr_surcharge"] = (
                total_distance * self._base_rates["adr_surcharge"]
            )
        
        # Temperature control costs
        if "Temperature controlled" in (cargo.special_requirements or []):
            cargo_costs["refrigeration"] = (
                total_distance * self._base_rates["refrigeration"]
            )
        
        # High-value cargo insurance
        if cargo.value and cargo.value > 100000:  # Threshold for high-value cargo
            cargo_costs["high_value_insurance"] = (
                cargo.value * self._base_rates["high_value"] * days
            )
        
        self.logger.info("cargo_costs_calculated", cargo_costs=cargo_costs)
        return cargo_costs
    
    def _get_cost_description(self, cost_type: str) -> str:
        """Get human-readable description for cost types"""
        self.logger.info("getting_cost_description", cost_type=cost_type)
        descriptions = {
            "fuel": "Fuel cost per kilometer",
            "driver": "Driver salary per hour",
            "toll": "Base toll rate per kilometer",
            "maintenance": "Vehicle maintenance per kilometer",
            "insurance": "Daily insurance cost",
            "overhead": "Daily overhead costs",
            "adr_surcharge": "ADR dangerous goods surcharge per kilometer",
            "refrigeration": "Temperature control cost per kilometer",
            "high_value": "High-value cargo insurance (% of value per day)",
        }
        description = descriptions.get(cost_type, "Miscellaneous cost")
        self.logger.info("cost_description_retrieved", description=description)
        return description
