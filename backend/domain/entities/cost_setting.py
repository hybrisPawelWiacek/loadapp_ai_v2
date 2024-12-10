from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4
from dateutil import tz

@dataclass
class CostSetting:
    """Domain entity representing a cost calculation setting."""
    
    # Basic information (required fields without defaults)
    name: str  # Human-readable name for the setting
    type: str  # Type of cost (e.g., fuel, maintenance)
    category: str  # Category for grouping (base, variable, cargo-specific)
    base_value: float  # Base cost value for calculations
    
    # Fields with default values
    id: UUID = field(default_factory=uuid4)  # Unique identifier for the setting
    multiplier: float = 1.0  # Multiplier applied to base value
    currency: str = "EUR"  # Currency for the cost values
    is_enabled: bool = True  # Whether this setting is active
    
    # Metadata
    description: Optional[str] = None  # Detailed description of the setting
    created_by: Optional[str] = None  # User who created the setting
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())  # Creation timestamp
    last_updated: datetime = field(default_factory=lambda: datetime.utcnow())  # Last update timestamp
    
    # Complex data with defaults
    validation_rules: Dict = field(default_factory=dict)  # Rules for validating the setting
    historical_data: Dict = field(default_factory=dict)  # Historical values and changes

    def __post_init__(self):
        """Ensure proper type conversion after initialization."""
        # Ensure id is a UUID object
        if isinstance(self.id, str):
            self.id = UUID(self.id)
            
        # Ensure datetimes are timezone-aware
        if self.created_at and not self.created_at.tzinfo:
            self.created_at = self.created_at.replace(tzinfo=tz.tzutc())
        if self.last_updated and not self.last_updated.tzinfo:
            self.last_updated = self.last_updated.replace(tzinfo=tz.tzutc())

    def apply_multiplier(self) -> float:
        """Calculate the effective cost value with multiplier applied."""
        return self.base_value * self.multiplier if self.is_enabled else 0.0

    def update(self, **kwargs) -> None:
        """Update setting fields and automatically set last_updated."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert the setting to a dictionary for serialization."""
        return {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'base_value': self.base_value,
            'multiplier': self.multiplier,
            'currency': self.currency,
            'is_enabled': self.is_enabled,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'validation_rules': self.validation_rules,
            'historical_data': self.historical_data
        }
