from dataclasses import dataclass

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address
        }
