from typing import Dict, List, Optional
import structlog
from ..entities import Route, CostItem

logger = structlog.get_logger(__name__)

class CostCalculationService:
    def __init__(self):
        self.logger = logger.bind(service="CostCalculationService")

    def calculate_total_cost(
        self,
        route: Route,
        cost_items: Optional[List[CostItem]] = None
    ) -> Dict[str, float]:
        """Calculate total cost and cost breakdown for a route."""
        self.logger.info(
            "calculating_costs",
            route_id=str(route.id),
            total_distance=route.main_route.distance_km + route.empty_driving.distance_km
        )

        # If no cost items provided, use default cost items
        if cost_items is None:
            cost_items = self._get_default_cost_items()

        # Calculate costs for each enabled cost item
        cost_breakdown = {}
        total_cost = 0.0

        for item in cost_items:
            if not item.is_enabled:
                continue

            # Calculate cost based on item type
            cost = self._calculate_item_cost(item, route)
            cost_breakdown[item.type] = cost
            total_cost += cost

        # Add total to the breakdown
        cost_breakdown["total"] = total_cost

        self.logger.info(
            "costs_calculated",
            route_id=str(route.id),
            total_cost=total_cost
        )

        return cost_breakdown

    def _calculate_item_cost(self, item: CostItem, route: Route) -> float:
        """Calculate cost for a specific cost item."""
        total_distance = route.main_route.distance_km + route.empty_driving.distance_km
        total_hours = route.total_duration_hours

        match item.type:
            case "fuel":
                # Base fuel cost per km * total distance * multiplier
                return item.base_value * total_distance * item.multiplier

            case "driver":
                # Hourly rate * total hours * multiplier
                return item.base_value * total_hours * item.multiplier

            case "tolls":
                # Fixed rate per country segment * number of segments * multiplier
                num_segments = len(route.main_route.country_segments)
                return item.base_value * num_segments * item.multiplier

            case "maintenance":
                # Base rate per km * total distance * multiplier
                return item.base_value * total_distance * item.multiplier

            case "insurance":
                # Fixed daily rate * ceil(total_hours/24) * multiplier
                days = (total_hours + 23) // 24  # Round up to full days
                return item.base_value * days * item.multiplier

            case _:
                # For unknown cost types, use base value * multiplier
                return item.base_value * item.multiplier

    def _get_default_cost_items(self) -> List[CostItem]:
        """Return default cost items with reasonable values."""
        from uuid import uuid4

        return [
            CostItem(
                id=uuid4(),
                type="fuel",
                category="variable",
                base_value=1.5,  # EUR per km
                description="Fuel cost per kilometer",
                multiplier=1.0,
                is_enabled=True
            ),
            CostItem(
                id=uuid4(),
                type="driver",
                category="variable",
                base_value=30.0,  # EUR per hour
                description="Driver wages per hour",
                multiplier=1.0,
                is_enabled=True
            ),
            CostItem(
                id=uuid4(),
                type="tolls",
                category="variable",
                base_value=50.0,  # EUR per country
                description="Average toll costs per country",
                multiplier=1.0,
                is_enabled=True
            ),
            CostItem(
                id=uuid4(),
                type="maintenance",
                category="variable",
                base_value=0.2,  # EUR per km
                description="Vehicle maintenance cost per kilometer",
                multiplier=1.0,
                is_enabled=True
            ),
            CostItem(
                id=uuid4(),
                type="insurance",
                category="fixed",
                base_value=100.0,  # EUR per day
                description="Daily insurance cost",
                multiplier=1.0,
                is_enabled=True
            )
        ]
