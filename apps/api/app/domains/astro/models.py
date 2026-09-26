from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any

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
    MEAN_NODE = "mean_node"
    SOUTH_NODE = "south_node"
    CHIRON = "chiron"


class HouseSystem(StrEnum):
    PLACIDUS = "placidus"
    WHOLE_SIGN = "whole_sign"
    EQUAL = "equal"


class Tradition(StrEnum):
    WESTERN = "western"
    JYOTISH = "jyotish"


class ZodiacMode(StrEnum):
    TROPICAL = "tropical"
    SIDEREAL = "sidereal"


class Ayanamsa(StrEnum):
    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"


class NodeMode(StrEnum):
    TRUE = "true"
    MEAN = "mean"


class CalculationConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    tradition: Tradition = Tradition.WESTERN
    zodiac: ZodiacMode = ZodiacMode.TROPICAL
    ayanamsa: Ayanamsa | None = None
    node_mode: NodeMode = NodeMode.TRUE
    house_system: HouseSystem = HouseSystem.PLACIDUS

    @model_validator(mode="before")
    @classmethod
    def apply_tradition_defaults(cls, value: Any) -> Any:
        if isinstance(value, dict) and value.get("tradition") in {
            Tradition.JYOTISH,
            Tradition.JYOTISH.value,
        }:
            return {"zodiac": ZodiacMode.SIDEREAL, **value}
        return value

    @model_validator(mode="after")
    def validate_tradition(self) -> CalculationConfig:
        if self.tradition is Tradition.JYOTISH:
            if self.zodiac is not ZodiacMode.SIDEREAL or self.ayanamsa is None:
                raise ValueError("Jyotish requires a sidereal zodiac and explicit ayanamsa")
        elif self.zodiac is not ZodiacMode.TROPICAL or self.ayanamsa is not None:
            raise ValueError("Western launch supports tropical zodiac without ayanamsa")
        return self

    @classmethod
    def western_recommended(cls) -> CalculationConfig:
        return cls()

    @classmethod
    def jyotish_recommended(cls) -> CalculationConfig:
        return cls(
            tradition=Tradition.JYOTISH,
            zodiac=ZodiacMode.SIDEREAL,
            ayanamsa=Ayanamsa.LAHIRI,
            house_system=HouseSystem.WHOLE_SIGN,
        )

    @property
    def fingerprint(self) -> str:
        payload = self.model_dump_json(exclude_none=False)
        return sha256(payload.encode()).hexdigest()[:24]


class ChartType(StrEnum):
    DATE_ONLY_NATAL = "date_only_natal"
    NATAL = "natal"
    DAILY_TRANSIT = "daily_transit"
    TRANSIT_TO_NATAL = "transit_to_natal"
    SYNASTRY = "synastry"
    COMPOSITE_MIDPOINT = "composite_midpoint"
    DAVISON_RELATIONSHIP = "davison_relationship"
    JYOTISH_NAVAMSA = "jyotish_navamsa"
    RELATIONSHIP_BUNDLE = "relationship_bundle"
    COMPATIBILITY_FACTS = "compatibility_facts"


class TimePrecision(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


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
    tradition: Tradition = Tradition.WESTERN
    zodiac: ZodiacMode = ZodiacMode.TROPICAL
    ayanamsa: Ayanamsa | None = None
    config_hash: str = "western-v1"


class NakshatraPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: BodyName
    name: str
    index: int = Field(ge=1, le=27)
    pada: int = Field(ge=1, le=4)
    degree_in_nakshatra: float = Field(ge=0, lt=360 / 27)


class GrahaDrishti(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_body: BodyName
    to_body: BodyName
    houses_apart: int = Field(ge=1, le=12)
    kind: str


class NatalChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.NATAL
    julian_day_ut: float
    bodies: tuple[BodyPosition, ...]
    houses: tuple[HousePosition, ...] | None
    angles: ChartAngles | None
    aspects: tuple[Aspect, ...]
    house_system: HouseSystem
    time_precision: TimePrecision = TimePrecision.EXACT
    provenance: EngineProvenance
    config: CalculationConfig = Field(default_factory=CalculationConfig.western_recommended)
    config_hash: str = "western-v1"
    nakshatras: tuple[NakshatraPosition, ...] = ()
    graha_drishti: tuple[GrahaDrishti, ...] = ()

    def body(self, name: BodyName) -> BodyPosition:
        for position in self.bodies:
            if position.body is name:
                return position
        raise KeyError(name)


class DateOnlySunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.DATE_ONLY_NATAL
    status: str
    sign: ZodiacSign | None
    candidates: tuple[ZodiacSign, ...]
    provenance: EngineProvenance


class TransitSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.DAILY_TRANSIT
    transit_date: date
    julian_day_ut: float
    bodies: tuple[BodyPosition, ...]
    provenance: EngineProvenance
    config: CalculationConfig = Field(default_factory=CalculationConfig.western_recommended)
    config_hash: str = "western-v1"


class TransitPhase(StrEnum):
    APPROACHING = "approaching"
    EXACT = "exact"
    SEPARATING = "separating"


class TransitToNatalContact(BaseModel):
    model_config = ConfigDict(frozen=True)

    transit_body: BodyName
    natal_body: BodyName
    kind: str
    exact_angle: float
    orb: float
    phase: TransitPhase


class TransitToNatalSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.TRANSIT_TO_NATAL
    observed_at: datetime
    contacts: tuple[TransitToNatalContact, ...]
    orb_policy_version: str
    provenance: EngineProvenance
    config: CalculationConfig = Field(default_factory=CalculationConfig.western_recommended)
    config_hash: str = "western-v1"


class RelationshipDimension(StrEnum):
    COMMUNICATION = "communication"
    EMOTIONAL = "emotional"
    RELATING = "relating"
    DRIVE = "drive"
    GROWTH = "growth"
    FRICTION = "friction"


class ContactTone(StrEnum):
    FLOW = "flow"
    ACTIVATION = "activation"
    MIXED = "mixed"


class SynastryContact(BaseModel):
    model_config = ConfigDict(frozen=True)

    body_a: BodyName
    body_b: BodyName
    kind: str
    orb: float
    exact_angle: float
    strength: float = Field(default=0, ge=0, le=1)
    tone: ContactTone = ContactTone.MIXED
    dimensions: tuple[RelationshipDimension, ...] = ()


class HouseOverlay(BaseModel):
    model_config = ConfigDict(frozen=True)

    body_owner: str = Field(pattern="^[ab]$")
    body: BodyName
    house_owner: str = Field(pattern="^[ab]$")
    house: int = Field(ge=1, le=12)
    target_house_system: HouseSystem


class SynastryFacts(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.SYNASTRY
    contacts: tuple[SynastryContact, ...]
    house_overlays: tuple[HouseOverlay, ...] = ()
    orb_policy_version: str = "synastry-orbs-v2"
    method_version: str = "synastry-v2"
    provenance: EngineProvenance


class CompositePoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: BodyName
    longitude: float
    sign: ZodiacSign
    degree_in_sign: float


class CompositeAspect(BaseModel):
    model_config = ConfigDict(frozen=True)

    body_a: BodyName
    body_b: BodyName
    kind: str
    exact_angle: float
    orb: float
    strength: float = Field(ge=0, le=1)


class CompositeChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.COMPOSITE_MIDPOINT
    method: str = "midpoint"
    points: tuple[CompositePoint, ...]
    aspects: tuple[CompositeAspect, ...] = ()
    orb_policy_version: str = "relationship-chart-orbs-v1"
    caveat: str = "Composite midpoint is a mathematical relationship chart, not a real sky moment."
    provenance: EngineProvenance


class DavisonRelationshipChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.DAVISON_RELATIONSHIP
    method: str = "uncorrected_temporal_geographic_midpoint_v1"
    midpoint_input: ChartInput
    chart: NatalChart
    caveat: str = (
        "Davison v1 uses the arithmetic midpoint of both UTC instants and locations; "
        "it is not the corrected Astrodienst method."
    )
    generated_interpretation_eligible: bool = False
    provenance: EngineProvenance


class NavamsaPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: BodyName
    source_longitude: float
    longitude: float
    sign: ZodiacSign
    degree_in_sign: float


class NavamsaChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.JYOTISH_NAVAMSA
    division: int = 9
    points: tuple[NavamsaPoint, ...]
    method_version: str = "navamsa-d9-v1"
    generated_interpretation_eligible: bool = False
    caveat: str = "Factual D9 positions only; relationship interpretation requires expert sign-off."
    provenance: EngineProvenance


class RelationshipDimensionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: RelationshipDimension
    contact_count: int = Field(ge=0)
    evidence_ids: tuple[str, ...]
    strongest_strength: float = Field(default=0, ge=0, le=1)


class RelationshipBundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.RELATIONSHIP_BUNDLE
    synastry: SynastryFacts
    composite: CompositeChart
    davison: DavisonRelationshipChart | None = None
    dimensions: tuple[RelationshipDimensionEvidence, ...]
    scalar_score_eligible: bool = False
    interpretation_gate: str = "conditional-reflection-v1"
    provenance: EngineProvenance


class CompatibilityScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = ChartType.COMPATIBILITY_FACTS
    moon_score: float = Field(ge=0, le=1)
    venus_score: float = Field(ge=0, le=1)
    mars_score: float = Field(ge=0, le=1)
    total_score: float = Field(ge=0, le=1)
    strongest_contacts: tuple[SynastryContact, ...]
    display_eligible: bool = False
    deprecated_reason: str = (
        "Use multidimensional RelationshipBundle evidence; do not show a score."
    )
    provenance: EngineProvenance
