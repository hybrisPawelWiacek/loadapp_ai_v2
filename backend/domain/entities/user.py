from dataclasses import dataclass, field
from typing import List
from uuid import UUID

@dataclass
class User:
    id: UUID
    name: str
    role: str = "transport_manager"
    permissions: List[str] = field(default_factory=lambda: ["full_access"])

@dataclass
class BusinessEntity:
    id: UUID
    name: str
    type: str
    operating_countries: List[str]
