from dataclasses import dataclass
from typing import Dict
from datetime import datetime
from uuid import UUID

@dataclass
class Offer:
    id: UUID
    route_id: UUID
    total_cost: float
    margin: float
    final_price: float
    fun_fact: str
    status: str
    created_at: datetime
    cost_breakdown: Dict[str, float]

    def to_dict(self) -> Dict:
        """Convert offer to a dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "route_id": str(self.route_id),
            "total_cost": self.total_cost,
            "margin": self.margin,
            "final_price": self.final_price,
            "fun_fact": self.fun_fact,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "cost_breakdown": self.cost_breakdown
        }
