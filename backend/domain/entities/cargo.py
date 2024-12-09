from dataclasses import dataclass, field
from typing import List
from uuid import UUID, uuid4

@dataclass
class Capacity:
    max_weight: float = 24000.0  # Default max weight in kg
    max_volume: float = 80.0     # Default max volume in m3
    unit: str = "metric"

@dataclass
class TransportType:
    name: str
    capacity: Capacity = field(default_factory=lambda: Capacity())
    restrictions: List[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

@dataclass
class Cargo:
    type: str
    weight: float
    value: float
    special_requirements: List[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
