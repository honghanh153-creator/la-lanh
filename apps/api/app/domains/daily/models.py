from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from app.domains.astro.models import TransitPhase


class PersonaMode(StrEnum):
    VIBE = "vibe"
    AURA = "aura"


class PersonaLabel(StrEnum):
    HOT = "Nóng"
    STEADY = "Bền"
    QUICK = "Lanh"
    SOFT = "Mềm"
    RADIANT = "Rực"
    NEAT = "Gọn"
    CHARMING = "Duyên"
    DEEP = "Sâu"
    WANDERING = "Phiêu"
    GROUNDED = "Chắc"
    DIFFERENT = "Khác"
    DREAMY = "Mộng"


class SourceLevel(StrEnum):
    DATE_ONLY_SUN = "date_only_sun"
    NATAL_CHART = "natal_chart"


class FallbackReason(StrEnum):
    AMBIGUOUS_SUN = "ambiguous_sun"
    INCOMPLETE_NATAL_CHART = "incomplete_natal_chart"
    MISSING_SUN = "missing_sun"
    LEGACY_ROW = "legacy_row"


@dataclass(frozen=True, slots=True)
class AuraAwakening:
    headline: str
    summary: str
    factors: tuple[str, ...]
    precision_label: str
    scoring_version: str
    confidence: str


@dataclass(frozen=True, slots=True)
class SkyChapter:
    title: str
    summary: str
    phase: TransitPhase
    phase_label: str
    signal_label: str
    orb: float
    observed_at: datetime
    orb_policy_version: str
    ranking_version: str
    disclaimer: str


@dataclass(frozen=True, slots=True)
class DailyNoteRecord:
    id: UUID
    guest_id: UUID
    note_date: date
    title: str
    body: str
    context_label: str
    content_version: str
    chart_snapshot_id: UUID | None
    created_at: datetime
    full_body: str = ""
    persona_mode: PersonaMode = PersonaMode.VIBE
    persona_label: PersonaLabel = PersonaLabel.SOFT
    persona_version: str = "persona-v1"
    source_level: SourceLevel = SourceLevel.DATE_ONLY_SUN
    astrology_source_version: str = "legacy"
    fallback_used: bool = True
    fallback_reason: FallbackReason | None = FallbackReason.LEGACY_ROW
    awakening: AuraAwakening | None = None
    sky_chapter: SkyChapter | None = None


@dataclass(frozen=True, slots=True)
class DailyNoteSnapshot:
    title: str
    body: str
    full_body: str
    context_label: str
    content_version: str
    persona_mode: PersonaMode
    persona_label: PersonaLabel
    persona_version: str
    source_level: SourceLevel
    astrology_source_version: str
    fallback_used: bool
    fallback_reason: FallbackReason | None
