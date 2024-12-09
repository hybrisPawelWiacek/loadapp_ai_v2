from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from pytz import UTC

class OfferStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class Currency(Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"

@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    validation_type: str
    severity: str = "error"  # error, warning, info

@dataclass
class BusinessRuleResult:
    rule_name: str
    passed: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OfferMetrics:
    total_value: float
    margin_percentage: float
    processing_time_ms: float
    ai_confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GeographicRestriction:
    allowed_countries: List[str]
    allowed_regions: List[str]
    restricted_zones: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "allowed_countries": self.allowed_countries,
            "allowed_regions": self.allowed_regions,
            "restricted_zones": self.restricted_zones,
            "metadata": self.metadata
        }

@dataclass
class CostBreakdown:
    base_costs: Dict[str, float]
    variable_costs: Dict[str, float]
    cargo_costs: Dict[str, Dict[str, float]]
    total_cost: float
    currency: Currency

    def validate(self) -> List[ValidationResult]:
        results = []
        if self.total_cost <= 0:
            results.append(ValidationResult(
                is_valid=False,
                message="Total cost must be positive",
                validation_type="cost",
                severity="error"
            ))
        
        # Calculate sum of all costs across categories
        total_from_categories = (
            sum(self.base_costs.values()) +
            sum(self.variable_costs.values()) +
            sum(sum(cargo_type_costs.values()) for cargo_type_costs in self.cargo_costs.values())
        )
        
        if abs(self.total_cost - total_from_categories) > 0.01:  # Allow small float rounding differences
            results.append(ValidationResult(
                is_valid=False,
                message="Cost breakdown does not sum up to total cost",
                validation_type="cost",
                severity="error"
            ))
        return results

    def to_dict(self) -> Dict:
        return {
            "base_costs": self.base_costs,
            "variable_costs": self.variable_costs,
            "cargo_costs": self.cargo_costs,
            "total_cost": self.total_cost,
            "currency": self.currency.value
        }

@dataclass
class OfferVersion:
    version: int
    changes: Dict[str, Any]
    changed_by: str
    changed_at: datetime
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Offer:
    id: UUID
    route_id: UUID
    cost_breakdown: CostBreakdown
    margin_percentage: float
    final_price: float
    currency: Currency
    status: OfferStatus
    created_at: datetime
    updated_at: datetime
    version: int
    created_by: str
    updated_by: str
    client_id: Optional[UUID] = None
    client_name: Optional[str] = None
    client_contact: Optional[str] = None
    geographic_restrictions: Optional[GeographicRestriction] = None
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    applied_settings: Dict[str, Any] = field(default_factory=dict)
    business_rules_validation: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _metrics: Optional[OfferMetrics] = None
    _validation_results: List[ValidationResult] = field(default_factory=list)
    _version_history: List[Dict] = field(default_factory=list)

    def validate(self) -> List[ValidationResult]:
        """Comprehensive validation of the offer."""
        results = []
        
        # Basic field validation
        if self.margin_percentage < 0 or self.margin_percentage > 100:
            results.append(ValidationResult(
                is_valid=False,
                message="Margin percentage must be between 0 and 100",
                validation_type="margin",
                severity="error"
            ))
            
        if self.final_price <= 0:
            results.append(ValidationResult(
                is_valid=False,
                message="Final price must be positive",
                validation_type="price",
                severity="error"
            ))
            
        # Cost breakdown validation
        results.extend(self.cost_breakdown.validate())
        
        # Geographic restrictions validation
        if self.geographic_restrictions:
            if not self.geographic_restrictions.allowed_countries and not self.geographic_restrictions.allowed_regions:
                results.append(ValidationResult(
                    is_valid=False,
                    message="At least one allowed country or region must be specified",
                    validation_type="geographic",
                    severity="error"
                ))
        
        # Business rules validation
        if not all(self.business_rules_validation.values()):
            failed_rules = [rule for rule, passed in self.business_rules_validation.items() if not passed]
            results.append(ValidationResult(
                is_valid=False,
                message=f"Failed business rules: {', '.join(failed_rules)}",
                validation_type="business_rules",
                severity="error"
            ))
        
        return results

    def calculate_metrics(self) -> OfferMetrics:
        """Calculate and update offer metrics."""
        if not self._metrics:
            self._metrics = OfferMetrics(
                total_value=self.final_price,
                margin_percentage=self.margin_percentage,
                processing_time_ms=0.0,  # This should be updated by the service
                ai_confidence_score=self.ai_insights.get('confidence_score', 0.0),
                metadata={
                    'cost_breakdown': self.cost_breakdown.__dict__,
                    'status': self.status.value,
                    'version': self.version
                }
            )
        return self._metrics

    def add_version(self, changed_by: str, changes: Dict[str, Any], reason: str):
        """Add a new version to the history."""
        self.version += 1
        version_data = {
            'id': uuid4(),
            'entity_id': self.id,
            'version': self.version,
            'data': {
                'route_id': str(self.route_id),
                'client_id': str(self.client_id) if self.client_id else None,
                'cost_breakdown': self.cost_breakdown.to_dict() if self.cost_breakdown else None,
                'margin_percentage': self.margin_percentage,
                'final_price': self.final_price,
                'currency': self.currency.value if self.currency else None,
                'status': self.status.value if self.status else None,
                'metadata': {
                    'client_name': self.client_name,
                    'client_contact': self.client_contact,
                    'geographic_restrictions': self.geographic_restrictions.to_dict() if self.geographic_restrictions else None,
                    'ai_insights': self.ai_insights,
                    'applied_settings': self.applied_settings,
                    'business_rules_validation': self.business_rules_validation
                }
            },
            'created_at': datetime.now(UTC),
            'created_by': changed_by,
            'change_reason': reason,
            'version_metadata': {'changes': changes}
        }
        self._version_history.append(version_data)

    def can_transition_to(self, new_status: OfferStatus) -> Tuple[bool, str]:
        """Check if the offer can transition to the new status."""
        valid_transitions = {
            OfferStatus.DRAFT: [OfferStatus.PENDING],
            OfferStatus.PENDING: [OfferStatus.SENT, OfferStatus.EXPIRED],
            OfferStatus.SENT: [OfferStatus.ACCEPTED, OfferStatus.REJECTED, OfferStatus.EXPIRED],
            OfferStatus.ACCEPTED: [OfferStatus.EXPIRED],
            OfferStatus.REJECTED: [],
            OfferStatus.EXPIRED: []
        }
        
        if new_status in valid_transitions.get(self.status, []):
            return True, ""
        return False, f"Invalid status transition from {self.status.value} to {new_status.value}"

    def to_dict(self) -> Dict:
        """Convert offer to a dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "route_id": str(self.route_id),
            "cost_breakdown": self.cost_breakdown.to_dict(),
            "margin_percentage": self.margin_percentage,
            "final_price": self.final_price,
            "currency": self.currency.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "client_id": str(self.client_id) if self.client_id else None,
            "client_name": self.client_name,
            "client_contact": self.client_contact,
            "geographic_restrictions": self.geographic_restrictions.to_dict() if self.geographic_restrictions else None,
            "ai_insights": self.ai_insights,
            "applied_settings": self.applied_settings,
            "business_rules_validation": self.business_rules_validation,
            "metadata": self.metadata,
            "metrics": self._metrics.__dict__ if self._metrics else None,
            "version_history": self._version_history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Offer':
        """Create an Offer instance from a dictionary."""
        # Convert string IDs to UUID
        data['id'] = UUID(data['id'])
        data['route_id'] = UUID(data['route_id'])
        data['client_id'] = UUID(data['client_id']) if data.get('client_id') else None
        
        # Convert string dates to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Convert string enums to proper enum types
        data['currency'] = Currency(data['currency'])
        data['status'] = OfferStatus(data['status'])
        
        # Convert nested structures
        data['cost_breakdown'] = CostBreakdown(**data['cost_breakdown'])
        if data.get('geographic_restrictions'):
            data['geographic_restrictions'] = GeographicRestriction(**data['geographic_restrictions'])
        if data.get('metrics'):
            data['metrics'] = OfferMetrics(**data['metrics'])
        if data.get('version_history'):
            data['_version_history'] = data['version_history']
        
        return cls(**data)
