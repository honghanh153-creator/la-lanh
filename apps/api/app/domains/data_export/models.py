"""Strict schema of the "Tải dữ liệu của tôi" file (right of access and portability).

Every model forbids extra fields, so a new column never leaks into the file by accident: it has
to be added here on purpose and reviewed against the inventory in
docs/plans/2026-10-29-privacy-export-and-b-rights.md.
No model carries a database id, hash, key, token, receipt or another person's birth data.
"""

from datetime import date, datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict

from app.domains.astro.models import DateOnlySunResult, NatalChart

EXPORT_FORMAT: Final = "la-lanh-data-export-v1"
# Newest items per list. A list that reached the bound is named in ``truncated``.
MAX_ITEMS_PER_SECTION = 500


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExportProfile(_Strict):
    state: str
    onboarding_status: str
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime


class ExportDevice(_Strict):
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class ExportAccount(_Strict):
    masked_email: str
    linked_at: datetime
    devices: list[ExportDevice]


class ExportConsent(_Strict):
    purpose: str
    version: str
    accepted_at: datetime
    revoked_at: datetime | None


class ExportHistoryRetention(_Strict):
    consent_version: str
    activated_at: datetime


class ExportBirthProfile(_Strict):
    birth_date: date
    profile_level: int
    time_precision: str
    birth_time_mode: str
    birth_time_local: str | None
    approx_window: str | None
    place_display_name: str | None
    timezone_id: str | None
    supplement_consent_version: str | None
    calculated_at: datetime
    calculation_kind: Literal["date_only_sun", "natal_chart"]
    calculation: DateOnlySunResult | NatalChart


class ExportDailyNote(_Strict):
    note_date: date
    title: str
    body: str
    full_body: str
    context_label: str
    persona_mode: str
    persona_label: str
    created_at: datetime
    mood: str | None
    mood_checked_in_at: datetime | None


class ExportReadingSections(_Strict):
    hook: str
    thesis: str
    manifestation: str
    transit: str | None
    micro_action: str
    companion: str | None


class ExportReadingEvidence(_Strict):
    title: str
    claims: list[str]
    framework_disclosure: str


class ExportSavedReading(_Strict):
    sections: ExportReadingSections
    evidence: ExportReadingEvidence
    disclaimer: str


class ExportSavedNote(_Strict):
    saved_at: datetime
    note_date: str | None
    title: str | None
    body: str | None
    full_body: str | None
    context_label: str | None
    persona_label: str | None
    reading: ExportSavedReading | None


class ExportShareLink(_Strict):
    format: str
    status: Literal["active", "revoked", "expired"]
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class ExportTarotCard(_Strict):
    position: str
    card: str


class ExportTarotPosition(_Strict):
    position: str
    card: str
    meaning_here: str
    everyday_scene: str
    reflection_question: str
    small_action: str | None


class ExportTarotReading(_Strict):
    headline: str
    summary: str
    positions: list[ExportTarotPosition]
    conclusion: str | None
    closing_prompt: str
    disclaimer: str


class ExportTarotSession(_Strict):
    state: str
    context: str
    spread: str
    voice: str
    question: str
    cards: list[ExportTarotCard]
    reading: ExportTarotReading | None
    created_at: datetime
    expires_at: datetime


class ExportNoteFeedback(_Strict):
    choice: str
    background_lens: str | None
    created_at: datetime
    expires_at: datetime


class ExportDailyExperiment(_Strict):
    state: str
    background_lens: str
    outcome: str | None
    created_at: datetime
    expires_at: datetime
    reflected_at: datetime | None


class ExportRadarSent(_Strict):
    """A's own side only: the nickname A typed and the request's lifecycle, never B's data."""

    nickname: str
    context: str
    voice: str
    mode: str
    status: str
    permission_attested_at: datetime | None
    created_at: datetime
    expires_at: datetime


class ExportRadarReceived(_Strict):
    """B's own side: B's consent, never the nickname the sender chose for B."""

    context: str
    consent_version: str | None
    accepted_at: datetime
    expires_at: datetime


class ExportLaChungInvite(_Strict):
    nickname: str
    context: str
    status: str
    has_response: bool
    created_at: datetime
    expires_at: datetime


class ExportMatchingProfile(_Strict):
    display_name: str
    gender_identity: str
    intent: str
    gender_preference: str
    min_age: int
    max_age: int
    region_code: str
    weekly_intent: str
    active: bool
    joined_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ExportMatching(_Strict):
    profile: ExportMatchingProfile | None
    consents: list[ExportConsent]
    verification_status: str | None


class DataExport(_Strict):
    format: Literal["la-lanh-data-export-v1"] = EXPORT_FORMAT
    generated_at: datetime
    notice: str
    profile: ExportProfile
    account: ExportAccount | None
    consents: list[ExportConsent]
    history_retention: ExportHistoryRetention | None
    birth_profile: ExportBirthProfile | None
    daily_notes: list[ExportDailyNote]
    saved_notes: list[ExportSavedNote]
    share_links: list[ExportShareLink]
    tarot_sessions: list[ExportTarotSession]
    note_feedback: list[ExportNoteFeedback]
    daily_experiments: list[ExportDailyExperiment]
    radar_sent: list[ExportRadarSent]
    radar_received: list[ExportRadarReceived]
    la_chung_invites: list[ExportLaChungInvite]
    matching: ExportMatching | None
    not_included: list[str]
    truncated: list[str]
