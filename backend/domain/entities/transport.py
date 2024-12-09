from dataclasses import dataclass
from uuid import UUID

@dataclass
class TruckDriverPair:
    id: UUID
    truck_type: str
    driver_id: str
    capacity: float
    availability: bool = True
