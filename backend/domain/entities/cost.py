from dataclasses import dataclass
from uuid import UUID
from typing import Dict, Any

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

    def __post_init__(self):
        # Ensure id is a UUID object
        if isinstance(self.id, str):
            self.id = UUID(self.id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CostItem to dictionary."""
        return {
            'id': str(self.id),
            'type': self.type,
            'category': self.category,
            'base_value': self.base_value,
            'description': self.description,
            'multiplier': self.multiplier,
            'currency': self.currency,
            'is_enabled': self.is_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostItem':
        """Create a CostItem from dictionary."""
        return cls(
            id=UUID(data['id']) if isinstance(data['id'], str) else data['id'],
            type=data['type'],
            category=data['category'],
            base_value=data['base_value'],
            description=data['description'],
            multiplier=data.get('multiplier', 1.0),
            currency=data.get('currency', 'EUR'),
            is_enabled=data.get('is_enabled', True)
        )

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
