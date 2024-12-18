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
        # Handle 'type' field if present
        if hasattr(self, 'type'):
            self.name = getattr(self, 'type')
            delattr(self, 'type')
        # Convert capacity if it's a dict
        if isinstance(self.capacity, dict):
            self.capacity = Capacity(**self.capacity)
    
    @classmethod
    def from_cargo(cls, cargo: 'Cargo') -> 'TransportType':
        """Create a TransportType instance from a Cargo object."""
        capacities = {
            "Standard Truck": Capacity(max_weight=24000, max_volume=80),
            "Small Truck": Capacity(max_weight=7500, max_volume=40),
            "Van": Capacity(max_weight=3500, max_volume=20),
        }
        
        transport_type = cargo.type if isinstance(cargo.type, str) else "Standard Truck"
        capacity = capacities.get(transport_type, Capacity(max_weight=24000, max_volume=80))
        
        return cls(
            name=transport_type,
            capacity=capacity,
            restrictions=[]
        )
    
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
