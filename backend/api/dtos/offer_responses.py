from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

@dataclass
class OfferResponse:
    """Data Transfer Object for Offer responses."""
    id: UUID
    route_id: UUID
    total_cost: float
    margin: float
    final_price: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    cost_breakdown: Dict[str, Any]
    applied_settings: Dict[str, Any]
    ai_insights: Dict[str, Any]
    geographic_restrictions: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DTO to a dictionary."""
        return {
            'id': str(self.id),
            'route_id': str(self.route_id),
            'total_cost': self.total_cost,
            'margin': self.margin,
            'final_price': self.final_price,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'cost_breakdown': self.cost_breakdown,
            'applied_settings': self.applied_settings,
            'ai_insights': self.ai_insights,
            'geographic_restrictions': self.geographic_restrictions,
            'metrics': self.metrics,
            'version': self.version
        } 