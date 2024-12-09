from dataclasses import dataclass
from uuid import UUID
from typing import Dict

@dataclass
class CostItem:
    id: UUID
    type: str
    category: str
    base_value: float
    description: str
    multiplier: float = 1.0
    currency: str = "EUR"
    is_enabled: bool = True

@dataclass
class Cost:
    total_cost: float
    fuel_cost: float
    driver_cost: float
    maintenance_cost: float
    toll_cost: float
    other_costs: float
    currency: str = "EUR"

    @classmethod
    def from_dict(cls, cost_dict: Dict[str, float]) -> 'Cost':
        """Create a Cost object from a dictionary of costs."""
        return cls(
            total_cost=cost_dict.get("total", 0.0),
            fuel_cost=cost_dict.get("fuel", 0.0),
            driver_cost=cost_dict.get("driver", 0.0),
            maintenance_cost=cost_dict.get("maintenance", 0.0),
            toll_cost=cost_dict.get("toll", 0.0),
            other_costs=sum(
                value for key, value in cost_dict.items()
                if key not in ["total", "fuel", "driver", "maintenance", "toll"]
            )
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert Cost object to dictionary."""
        return {
            "fuel": self.fuel_cost,
            "driver": self.driver_cost,
            "maintenance": self.maintenance_cost,
            "toll": self.toll_cost,
            "other": self.other_costs,
            "total": self.total_cost
        }
