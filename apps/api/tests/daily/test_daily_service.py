from datetime import UTC, datetime

import pytest

from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    DateOnlySunResult,
    EngineProvenance,
    HouseSystem,
    NatalChart,
    TransitPhase,
    TransitToNatalContact,
    ZodiacSign,
)
from app.domains.daily.models import FallbackReason, PersonaMode
from app.domains.daily.service import (
    PERSONA_LABELS,
    PRODUCT_TIMEZONE,
    SIGN_COPY,
    _awakening_for,
    _chapter_for,
    _snapshot_for,
)

PROVENANCE = EngineProvenance(version="2.10.03", profile="test")


def test_product_timezone_rolls_daily_note_at_vietnam_midnight() -> None:
    instant = datetime(2026, 9, 7, 18, tzinfo=UTC)

    assert instant.astimezone(PRODUCT_TIMEZONE).date().isoformat() == "2026-09-08"


@pytest.mark.parametrize(
    ("sign", "label"),
    [
        (ZodiacSign.ARIES, "Nóng"),
        (ZodiacSign.TAURUS, "Bền"),
        (ZodiacSign.GEMINI, "Lanh"),
        (ZodiacSign.CANCER, "Mềm"),
        (ZodiacSign.LEO, "Rực"),
        (ZodiacSign.VIRGO, "Gọn"),
        (ZodiacSign.LIBRA, "Duyên"),
        (ZodiacSign.SCORPIO, "Sâu"),
        (ZodiacSign.SAGITTARIUS, "Phiêu"),
        (ZodiacSign.CAPRICORN, "Chắc"),
        (ZodiacSign.AQUARIUS, "Khác"),
        (ZodiacSign.PISCES, "Mộng"),
    ],
)
def test_date_only_sun_uses_approved_vibe_labels(sign: ZodiacSign, label: str) -> None:
    result = DateOnlySunResult(
        status="certain",
        sign=sign,
        candidates=(sign,),
        provenance=PROVENANCE,
    )

    note = _snapshot_for(result)

    assert PERSONA_LABELS[sign].value == label
    assert note.persona_mode is PersonaMode.VIBE
    assert note.persona_label.value == label
    assert note.context_label.startswith("Mặt Trời ")
    assert note.fallback_used is False
    assert note.fallback_reason is None
    assert 80 <= len(note.full_body.split()) <= 140


def test_weighted_personal_plan_outweighs_raw_outer_planet_counts() -> None:
    signs = [
        ZodiacSign.TAURUS,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.GEMINI,
        ZodiacSign.LIBRA,
    ]

    note = _snapshot_for(_natal_chart(signs))

    assert note.persona_mode is PersonaMode.AURA
    assert note.persona_label.value == "Rực"
    assert note.context_label == "Lửa · Khởi xướng · Mặt Trời Kim Ngưu"
    assert note.fallback_used is False
    assert note.title != SIGN_COPY[ZodiacSign.TAURUS][0]
    assert "Mặt Trời" in note.full_body
    assert "Mặt Trăng" in note.full_body
    assert "Sao Kim" in note.full_body


def test_aura_evidence_changes_when_personal_planets_change() -> None:
    first = _natal_chart([ZodiacSign.TAURUS] * 12)
    second = _natal_chart(
        [
            ZodiacSign.TAURUS,
            ZodiacSign.GEMINI,
            ZodiacSign.CANCER,
            ZodiacSign.LEO,
            ZodiacSign.VIRGO,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
            ZodiacSign.TAURUS,
        ]
    )

    assert _awakening_for(first).factors != _awakening_for(second).factors
    assert "Mặt Trăng · Song Tử" in _awakening_for(second).factors
    assert _snapshot_for(first).full_body != _snapshot_for(second).full_body


def test_sky_chapter_salience_can_prefer_slow_context_over_tighter_moon() -> None:
    contacts = (
        TransitToNatalContact(
            transit_body=BodyName.MOON,
            natal_body=BodyName.SUN,
            kind="conjunction",
            exact_angle=0.0,
            orb=0.5,
            phase=TransitPhase.APPROACHING,
        ),
        TransitToNatalContact(
            transit_body=BodyName.PLUTO,
            natal_body=BodyName.SUN,
            kind="conjunction",
            exact_angle=0.0,
            orb=0.6,
            phase=TransitPhase.APPROACHING,
        ),
    )

    chapter = _chapter_for(contacts, datetime(2026, 9, 6, 12, tzinfo=UTC))

    assert chapter is not None
    assert chapter.signal_label.startswith("Diêm Vương x Mặt Trời")


@pytest.mark.parametrize(
    ("sign", "label"),
    [
        (ZodiacSign.ARIES, "Rực"),
        (ZodiacSign.TAURUS, "Chắc"),
        (ZodiacSign.GEMINI, "Lanh"),
        (ZodiacSign.CANCER, "Mềm"),
    ],
)
def test_complete_natal_maps_each_dominant_element_to_aura(sign: ZodiacSign, label: str) -> None:
    note = _snapshot_for(_natal_chart([sign] * 12))

    assert note.persona_mode is PersonaMode.AURA
    assert note.persona_label.value == label


def test_complete_natal_tie_uses_fixed_element_order_when_sun_is_not_tied() -> None:
    signs = [
        ZodiacSign.GEMINI,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.ARIES,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.TAURUS,
        ZodiacSign.LIBRA,
    ]

    note = _snapshot_for(_natal_chart(signs))

    assert note.persona_mode is PersonaMode.AURA
    assert note.persona_label.value == "Rực"
    assert note.context_label == "Lửa · Khởi xướng · Mặt Trời Song Tử"


def test_incomplete_natal_falls_back_to_sun_vibe_without_claiming_aura() -> None:
    result = _natal_chart([ZodiacSign.SCORPIO], bodies=(BodyName.SUN,))

    note = _snapshot_for(result)

    assert note.persona_mode is PersonaMode.VIBE
    assert note.persona_label.value == "Sâu"
    assert note.context_label == "Mặt Trời Bọ Cạp"
    assert note.fallback_used is True
    assert note.fallback_reason is FallbackReason.INCOMPLETE_NATAL_CHART


def test_natal_without_sun_uses_neutral_vibe() -> None:
    bodies = tuple(body for body in BodyName if body is not BodyName.SUN)
    result = _natal_chart([ZodiacSign.LEO] * len(bodies), bodies=bodies)

    note = _snapshot_for(result)

    assert note.persona_mode is PersonaMode.VIBE
    assert note.persona_label.value == "Mềm"
    assert note.context_label == "Chưa chốt được cung Mặt Trời"
    assert note.fallback_reason is FallbackReason.MISSING_SUN


def test_ambiguous_date_only_result_uses_reviewed_neutral_vibe() -> None:
    result = DateOnlySunResult(
        status="candidates",
        sign=None,
        candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
        provenance=PROVENANCE,
    )

    note = _snapshot_for(result)

    assert note.persona_mode is PersonaMode.VIBE
    assert note.persona_label.value == "Mềm"
    assert note.context_label == "Chưa chốt được cung Mặt Trời"
    assert note.fallback_used is True
    assert note.fallback_reason is FallbackReason.AMBIGUOUS_SUN
    assert 80 <= len(note.full_body.split()) <= 140


def _natal_chart(
    signs: list[ZodiacSign],
    *,
    bodies: tuple[BodyName, ...] = (
        BodyName.SUN,
        BodyName.MOON,
        BodyName.MERCURY,
        BodyName.VENUS,
        BodyName.MARS,
        BodyName.JUPITER,
        BodyName.SATURN,
        BodyName.URANUS,
        BodyName.NEPTUNE,
        BodyName.PLUTO,
        BodyName.TRUE_NODE,
        BodyName.CHIRON,
    ),
) -> NatalChart:
    positions = tuple(
        BodyPosition(
            body=body,
            longitude=index * 30.0,
            latitude=0.0,
            distance_au=1.0,
            longitude_speed=1.0,
            retrograde=False,
            sign=sign,
            degree_in_sign=0.0,
        )
        for index, (body, sign) in enumerate(zip(bodies, signs, strict=True))
    )
    return NatalChart(
        julian_day_ut=2_460_000.5,
        bodies=positions,
        houses=None,
        angles=None,
        aspects=(),
        house_system=HouseSystem.PLACIDUS,
        provenance=PROVENANCE,
    )
