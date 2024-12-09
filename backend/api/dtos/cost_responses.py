from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID

@dataclass
class CostSettingMetadata:
    """Metadata about a cost setting's usage and impact."""
    last_used: Optional[datetime] = None
    usage_count: int = 0
    average_impact: float = 0.0
    confidence_score: float = 1.0

@dataclass
class CostSettingResponse:
    """Response DTO for cost settings."""
    id: UUID
    type: str
    category: str
    base_value: float
    multiplier: float
    currency: str
    is_enabled: bool
    description: Optional[str] = None
    last_updated: Optional[datetime] = None
    impact_analysis: Dict = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)
    metadata: CostSettingMetadata = field(default_factory=CostSettingMetadata)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "type": self.type,
            "category": self.category,
            "base_value": self.base_value,
            "multiplier": self.multiplier,
            "currency": self.currency,
            "is_enabled": self.is_enabled,
            "description": self.description,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "impact_analysis": self.impact_analysis,
            "optimization_suggestions": self.optimization_suggestions,
            "metadata": {
                "last_used": self.metadata.last_used.isoformat() if self.metadata.last_used else None,
                "usage_count": self.metadata.usage_count,
                "average_impact": self.metadata.average_impact,
                "confidence_score": self.metadata.confidence_score
            }
        }

@dataclass
class CostBreakdownItem:
    """Detailed breakdown of a specific cost component."""
    base_amount: float
    adjustments: Dict[str, float]
    final_amount: float
    applied_settings: List[UUID]
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "base_amount": self.base_amount,
            "adjustments": self.adjustments,
            "final_amount": self.final_amount,
            "applied_settings": [str(s) for s in self.applied_settings],
            "notes": self.notes
        }

@dataclass
class OptimizationInsight:
    """Optimization insight for a cost calculation."""
    potential_savings: float
    confidence_score: float
    suggestions: List[str]
    impact_areas: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "potential_savings": self.potential_savings,
            "confidence_score": self.confidence_score,
            "suggestions": self.suggestions,
            "impact_areas": self.impact_areas
        }

@dataclass
class CostBreakdownResponse:
    """Response DTO for cost breakdowns."""
    total_cost: float
    currency: str
    breakdown: Dict[str, CostBreakdownItem]
    applied_settings: List[CostSettingResponse]
    optimization_potential: float
    accuracy_score: float
    calculation_time_ms: float
    optimization_insights: Optional[OptimizationInsight] = None
    warnings: List[str] = field(default_factory=list)
    calculation_id: Optional[UUID] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_cost": self.total_cost,
            "currency": self.currency,
            "breakdown": {
                category: item.to_dict() 
                for category, item in self.breakdown.items()
            },
            "applied_settings": [
                setting.to_dict() for setting in self.applied_settings
            ],
            "optimization_potential": self.optimization_potential,
            "accuracy_score": self.accuracy_score,
            "calculation_time_ms": self.calculation_time_ms,
            "optimization_insights": (
                self.optimization_insights.to_dict() 
                if self.optimization_insights 
                else None
            ),
            "warnings": self.warnings,
            "calculation_id": str(self.calculation_id) if self.calculation_id else None
        }

# Example JSON response:
"""
{
    "total_cost": 1250.75,
    "currency": "EUR",
    "breakdown": {
        "fuel": {
            "base_amount": 800.0,
            "adjustments": {
                "distance_multiplier": 1.2,
                "seasonal_adjustment": 0.95
            },
            "final_amount": 912.0,
            "applied_settings": ["uuid1", "uuid2"],
            "notes": "Includes winter fuel adjustment"
        },
        "maintenance": {
            "base_amount": 300.0,
            "adjustments": {
                "vehicle_age": 1.1
            },
            "final_amount": 330.0,
            "applied_settings": ["uuid3"],
            "notes": null
        }
    },
    "applied_settings": [
        {
            "id": "uuid1",
            "type": "fuel",
            "category": "base",
            "base_value": 1.8,
            "multiplier": 1.2,
            "currency": "EUR",
            "is_enabled": true,
            "description": "Standard fuel rate",
            "last_updated": "2024-12-09T10:30:00Z",
            "impact_analysis": {
                "cost_impact": "high",
                "usage_frequency": "daily"
            },
            "optimization_suggestions": [
                "Consider bulk fuel contracts"
            ],
            "metadata": {
                "last_used": "2024-12-09T11:00:00Z",
                "usage_count": 150,
                "average_impact": 0.35,
                "confidence_score": 0.95
            }
        }
    ],
    "optimization_potential": 85.50,
    "accuracy_score": 0.98,
    "calculation_time_ms": 45.2,
    "optimization_insights": {
        "potential_savings": 85.50,
        "confidence_score": 0.9,
        "suggestions": [
            "Optimize fuel consumption",
            "Review maintenance schedule"
        ],
        "impact_areas": [
            "fuel_efficiency",
            "route_optimization"
        ]
    },
    "warnings": [
        "Seasonal fuel rates will be updated next month"
    ],
    "calculation_id": "uuid-calculation-123"
}
"""
