from dataclasses import dataclass, field
from typing import List
from uuid import UUID, uuid4

@dataclass
class Capacity:
    max_weight: float = 24000.0  # Default max weight in kg
    max_volume: float = 80.0     # Default max volume in m3
    unit: str = "metric"
    
    def to_dict(self) -> dict:
        """Convert capacity to dictionary for JSON serialization."""
        return {
            "max_weight": self.max_weight,
            "max_volume": self.max_volume,
            "unit": self.unit
        }

@dataclass
class TransportType:
    name: str
    capacity: Capacity = field(default_factory=lambda: Capacity())
    restrictions: List[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Ensure proper type conversion after initialization."""
        # Ensure id is a UUID object
        if isinstance(self.id, str):
            self.id = UUID(self.id)
    
    def to_dict(self) -> dict:
        """Convert transport type to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "capacity": self.capacity.to_dict(),
            "restrictions": self.restrictions,
            "id": str(self.id)
        }

@dataclass
class Cargo:
    type: str
    weight: float
    value: float
    special_requirements: List[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Ensure proper type conversion after initialization."""
        # Ensure id is a UUID object
        if isinstance(self.id, str):
            self.id = UUID(self.id)
    
    def to_dict(self) -> dict:
        """Convert cargo to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "weight": self.weight,
            "value": self.value,
            "special_requirements": self.special_requirements,
            "id": str(self.id)
        }
