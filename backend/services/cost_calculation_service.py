from typing import Dict, Any
from datetime import datetime, timedelta
from backend.infrastructure.database.repository import Repository
import structlog

logger = structlog.get_logger(__name__)

class CostCalculationService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self._cost_settings = {}
        self._load_cost_settings()

    def _load_cost_settings(self):
        """Load cost settings from the database"""
        settings = self.repository.get_enabled_cost_settings()
        self._cost_settings = {setting.name: setting for setting in settings}

    def calculate_costs(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs for a given route"""
        try:
            # Extract route parameters
            distance_km = float(route_data.get('distance', 0)) / 1000  # convert meters to kilometers
            duration_minutes = float(route_data.get('duration', 0)) / 60  # convert seconds to minutes
            
            # Convert duration to hours for calculations
            duration_hours = duration_minutes / 60

            # Calculate individual cost components
            fuel_cost = self._calculate_fuel_cost(distance_km)
            driver_cost = self._calculate_driver_cost(duration_hours)
            toll_cost = self._calculate_toll_cost(distance_km)
            maintenance_cost = self._calculate_maintenance_cost(distance_km)
            insurance_cost = self._calculate_insurance_cost(duration_hours)
            overhead_cost = self._calculate_overhead_cost(duration_hours)

            # Calculate main cost components
            base_cost = insurance_cost + overhead_cost
            distance_cost = fuel_cost + toll_cost + maintenance_cost
            time_cost = driver_cost

            # Calculate total cost
            total_cost = base_cost + distance_cost + time_cost

            return {
                'total_cost': total_cost,
                'breakdown': {
                    'base_cost': base_cost,
                    'distance_cost': distance_cost,
                    'time_cost': time_cost,
                    'fuel_cost': fuel_cost,
                    'driver_cost': driver_cost,
                    'toll_cost': toll_cost,
                    'maintenance_cost': maintenance_cost,
                    'insurance_cost': insurance_cost,
                    'overhead_cost': overhead_cost
                }
            }

        except Exception as e:
            logger.error("cost_calculation_failed", error=str(e), route_data=route_data)
            raise

    def _get_cost_value(self, setting_name: str, default: float = 0.0) -> float:
        """Get cost setting value with fallback to default"""
        setting = self._cost_settings.get(setting_name)
        if setting and setting.is_enabled:
            return float(setting.value) * float(setting.multiplier)
        return default

    def _calculate_fuel_cost(self, distance_km: float) -> float:
        return distance_km * self._get_cost_value('fuel_cost', 1.5)

    def _calculate_driver_cost(self, duration_hours: float) -> float:
        return duration_hours * self._get_cost_value('driver_cost', 30.0)

    def _calculate_toll_cost(self, distance_km: float) -> float:
        return distance_km * self._get_cost_value('toll_cost', 0.2)

    def _calculate_maintenance_cost(self, distance_km: float) -> float:
        return distance_km * self._get_cost_value('maintenance_cost', 0.1)

    def _calculate_insurance_cost(self, duration_hours: float) -> float:
        # Convert daily rate to hourly
        daily_rate = self._get_cost_value('insurance_cost', 100.0)
        return (daily_rate / 24) * duration_hours

    def _calculate_overhead_cost(self, duration_hours: float) -> float:
        # Convert daily rate to hourly
        daily_rate = self._get_cost_value('overhead_cost', 200.0)
        return (daily_rate / 24) * duration_hours
