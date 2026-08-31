from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ZodiacSign(StrEnum):
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


class BodyName(StrEnum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    TRUE_NODE = "true_node"
    CHIRON = "chiron"


class HouseSystem(StrEnum):
    PLACIDUS = "placidus"
    WHOLE_SIGN = "whole_sign"


class ChartInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    utc_datetime: datetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    house_system: HouseSystem = HouseSystem.PLACIDUS

    @model_validator(mode="after")
    def validate_location_pair(self) -> ChartInput:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        if self.utc_datetime.tzinfo is None or self.utc_datetime.utcoffset() is None:
            raise ValueError("utc_datetime must be timezone-aware")
        return self


class BodyPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: BodyName
    longitude: float
    latitude: float
    distance_au: float
    longitude_speed: float
    retrograde: bool
    sign: ZodiacSign
    degree_in_sign: float


class HousePosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1, le=12)
    longitude: float
    sign: ZodiacSign


class ChartAngles(BaseModel):
    model_config = ConfigDict(frozen=True)

    ascendant: float
    midheaven: float
    armc: float
    vertex: float


class Aspect(BaseModel):
    model_config = ConfigDict(frozen=True)

    body_a: BodyName
    body_b: BodyName
    kind: str
    exact_angle: float
    orb: float
    applying: bool


class EngineProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine: str = "swiss_ephemeris"
    version: str
    release_commit: str = "af9823fe7b06ffefe3d3968fdc5680be8b5eec5f"
    ephemeris_set: str = "de441-se1-1800-2399"
    profile: str


class NatalChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    julian_day_ut: float
    bodies: tuple[BodyPosition, ...]
    houses: tuple[HousePosition, ...] | None
    angles: ChartAngles | None
    aspects: tuple[Aspect, ...]
    provenance: EngineProvenance


class DateOnlySunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    birth_date: date
    status: str
    sign: ZodiacSign | None
    candidates: tuple[ZodiacSign, ...]
    interval_start_utc: datetime
    interval_end_utc: datetime
    provenance: EngineProvenance
