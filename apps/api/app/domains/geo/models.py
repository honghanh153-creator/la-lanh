from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlaceResult:
    place_id: str
    display_name: str
    country_code: str
    timezone_id: str
    latitude: float
    longitude: float
    confidence: str = "city"
