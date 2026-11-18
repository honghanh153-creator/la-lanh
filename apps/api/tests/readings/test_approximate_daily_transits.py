"""Daily step 2 wiring: an approximate Daily may carry a transit proven over the birth window.

Synthetic charts only (a fixed 1994 instant read as an approximate window); no real data.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domains.astro.aspects import INTERVAL_TRANSIT_ORB_VERSION
from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput, NatalChart, TimePrecision
from app.domains.daily.interval_transits import interval_transit_to_natal
from app.domains.readings.daily_psychology import DAILY_PSYCHOLOGY_MATRIX_VERSION
from app.domains.readings.daily_rotation import (
    VARIETY_KEY_VERSION,
    daily_variety_seed,
    day_index,
    derive_variety_key,
)
from app.domains.readings.models import (
    BackgroundLens,
    DailyVariety,
    FactorSource,
    ReadingPlan,
    ReadingPurpose,
    canonical_reading_plan_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import (
    DeterministicVietnameseRenderer,
    canonical_evidence_claim,
    plan_evidence_claim,
)

_ENGINE = NatalChartEngine()
# The synthetic chart is stored at 08:00 UTC, the 15:00 midpoint of a Vietnam afternoon window.
_ZONE = "Asia/Ho_Chi_Minh"
_KEY = derive_variety_key(b"test-only-server-secret")
_DAYS = [date(2026, 11, 1) + timedelta(days=offset) for offset in range(28)]


def _approximate() -> NatalChart:
    chart = _ENGINE.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1994, 7, 21, 8, tzinfo=UTC), latitude=21.03, longitude=105.85
        )
    )
    return chart.model_copy(
        update={"time_precision": TimePrecision.APPROXIMATE, "houses": None, "angles": None}
    )


def _variety(person: int, day: date) -> DailyVariety:
    return DailyVariety(
        key_version=VARIETY_KEY_VERSION,
        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
        seed=daily_variety_seed(_KEY, UUID(int=person + 1), DAILY_PSYCHOLOGY_MATRIX_VERSION),
        day_index=day_index(day),
    )


def _plan(
    chart: NatalChart, day: date, person: int = 0, lens: BackgroundLens | None = None
) -> ReadingPlan:
    observed = datetime.combine(day, time(5), tzinfo=UTC)
    return ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=interval_transit_to_natal(_ENGINE, chart, observed, birth_timezone=_ZONE),
        editorial_seed=day.isoformat(),
        daily_variety=_variety(person, day),
        background_lens=lens,
    )


def _transit_plans() -> list[ReadingPlan]:
    chart = _approximate()
    plans = [_plan(chart, day, person) for person in range(3) for day in _DAYS]
    return [p for p in plans if any(f.source is FactorSource.TRANSIT for f in p.factors)]


def test_an_approximate_daily_can_carry_a_window_proven_transit_and_names_its_policy() -> None:
    chart = _approximate()
    plans = [_plan(chart, day, person) for person in range(3) for day in _DAYS]
    with_transit = [p for p in plans if any(f.source is FactorSource.TRANSIT for f in p.factors)]
    assert with_transit, "over 28 days some approximate Daily uses a proven transit"
    for plan in plans:
        transit = [f for f in plan.factors if f.source is FactorSource.TRANSIT]
        assert plan.precision is TimePrecision.APPROXIMATE
        assert all("moon" not in f.subjects for f in plan.factors)
        if transit:
            assert plan.transit_policy == INTERVAL_TRANSIT_ORB_VERSION
            assert plan.daily_selection is not None
            assert plan.daily_selection.transit_ref == transit[0].id
            # The touched natal placement is one of the plan's time-stable placements.
            assert set(transit[0].child_refs) <= {f.id for f in plan.factors}
        else:
            assert plan.transit_policy is None


def test_the_evidence_of_a_window_plan_shows_no_orb_number() -> None:
    plan = _transit_plans()[0]
    transit = next(f for f in plan.factors if f.source is FactorSource.TRANSIT)
    claim = plan_evidence_claim(plan, transit)
    assert "orb" not in claim.display_text and "°" not in claim.display_text
    assert "pha" in claim.display_text
    orb_slot = next(slot for slot in claim.slots if slot.name.value == "orb")
    assert orb_slot.value.startswith("≤")
    # A point plan keeps the measured orb as before.
    assert "orb" in canonical_evidence_claim(transit).display_text
    candidate = DeterministicVietnameseRenderer().render(plan)
    shown = [c for c in candidate.evidence.claims if c.factor_ref == transit.id]
    assert shown and all("orb" not in c.display_text for c in shown)
    for text in (candidate.transit or "", candidate.hook, candidate.thesis):
        assert "orb" not in text


def test_a_lens_keeps_the_natal_evidence_and_any_transit_it_brings_is_window_proven() -> None:
    """US-03 AC22 with a transit. A lens picks among the situations of its arena, and a transit
    is attached only when it explains the picked situation, so a lens can change whether a
    transit appears (exact charts already do: the gap is tracked for both precisions). What a
    lens never changes: precision, the time-stable placements, and the proof of a transit."""

    chart = _approximate()
    renderer = DeterministicVietnameseRenderer()
    for person in range(3):
        for day in _DAYS:
            plain = _plan(chart, day, person)
            natal = {f.id for f in plain.factors if f.source is not FactorSource.TRANSIT}
            for lens in (BackgroundLens.WORK, BackgroundLens.RELATIONSHIPS, BackgroundLens.ENERGY):
                framed = _plan(chart, day, person, lens)
                assert framed.precision is plain.precision is TimePrecision.APPROXIMATE
                assert {f.id for f in framed.factors if f.source is not FactorSource.TRANSIT} == (
                    natal
                )
                transit = [f for f in framed.factors if f.source is FactorSource.TRANSIT]
                assert (framed.transit_policy is not None) == bool(transit)
                claims = renderer.render(framed).evidence.claims
                assert natal <= {c.factor_ref for c in claims}
                assert all(
                    "orb" not in c.display_text
                    for c in claims
                    if c.factor_ref.startswith("transit:")
                )


def test_snapshots_must_match_the_precision() -> None:
    chart = _approximate()
    observed = datetime(2026, 11, 3, 5, tzinfo=UTC)
    exact = chart.model_copy(update={"time_precision": TimePrecision.EXACT})
    interval = interval_transit_to_natal(_ENGINE, chart, observed, birth_timezone=_ZONE)
    with pytest.raises(ValueError, match="only for an approximate"):
        ReadingPlanner().plan(exact, purpose=ReadingPurpose.DAILY_NOTE, transits=interval)
    point = _ENGINE.calculate_transit_to_natal(chart, observed)
    with pytest.raises(ValueError, match="only a window-proven"):
        ReadingPlanner().plan(chart, purpose=ReadingPurpose.DAILY_NOTE, transits=point)


def test_the_plan_field_is_validated_and_absent_plans_keep_their_identity() -> None:
    plan = _transit_plans()[0]
    data = plan.model_dump()
    with pytest.raises(ValidationError, match="unsupported interval transit policy"):
        ReadingPlan.model_validate({**data, "transit_policy": "transit-orbs-v1+interval-v9"})
    natal_only = _plan(_approximate(), _DAYS[0], 7).model_copy(update={"transit_policy": None})
    if not any(f.source is FactorSource.TRANSIT for f in natal_only.factors):
        with pytest.raises(ValidationError, match="only an approximate Daily with a transit"):
            ReadingPlan.model_validate(
                {**natal_only.model_dump(), "transit_policy": INTERVAL_TRANSIT_ORB_VERSION}
            )
    # A plan without the field keys exactly as before the field existed.
    stored = natal_only.model_dump(mode="json")
    stored.pop("transit_policy")
    reread = ReadingPlan.model_validate(stored)
    assert canonical_reading_plan_key(reread) == canonical_reading_plan_key(natal_only)
    # An older reader ignores the field (pydantic's default); the policy is part of the identity.
    assert canonical_reading_plan_key(plan) != canonical_reading_plan_key(
        plan.model_copy(update={"transit_policy": None})
    )


def test_the_reading_service_reads_the_birthplace_zone_and_fails_closed() -> None:
    """Codex point 1: the zone comes from the stored birthplace; any failure means the wide
    window, never a guessed zone."""

    import asyncio
    from typing import Any, cast

    from app.domains.astro.aspects import INTERVAL_TRANSIT_ORB_VERSION as POLICY
    from app.domains.birth.errors import BirthProfileNotFound
    from app.domains.birth.models import BirthSupplementState, BirthTimeMode
    from app.domains.birth.service import BirthChartService
    from app.domains.readings.application import ReadingApplicationService

    guest = UUID(int=11)
    profile = UUID(int=12)
    calls: list[tuple[UUID, UUID]] = []

    async def lookup(guest_id: UUID, profile_id: UUID) -> str | None:
        calls.append((guest_id, profile_id))
        return _ZONE

    async def broken(guest_id: UUID, profile_id: UUID) -> str | None:
        raise RuntimeError("store unavailable")

    chart = _approximate()
    service = ReadingApplicationService(cast(Any, object()), _ENGINE, birth_timezone_lookup=lookup)
    assert asyncio.run(service._birth_timezone(guest, profile, chart)) == _ZONE
    assert calls == [(guest, profile)]
    exact = chart.model_copy(update={"time_precision": TimePrecision.EXACT})
    assert asyncio.run(service._birth_timezone(guest, profile, exact)) is None
    assert len(calls) == 1, "an exact chart never reads the birthplace"
    failing = ReadingApplicationService(cast(Any, object()), _ENGINE, birth_timezone_lookup=broken)
    assert asyncio.run(failing._birth_timezone(guest, profile, chart)) is None
    observed = datetime(2026, 11, 3, 5, tzinfo=UTC)
    snapshot = asyncio.run(
        service._optional_transits(chart, ReadingPurpose.DAILY_NOTE, observed, birth_timezone=_ZONE)
    )
    assert snapshot is not None and snapshot.orb_policy_version == POLICY
    assert (
        asyncio.run(service._optional_transits(chart, ReadingPurpose.READING_DETAIL, observed))
        is None
    ), "only the Daily takes window transits"

    # The birth service gives the zone only for the same profile.
    birth = BirthChartService.__new__(BirthChartService)

    async def state(guest_id: UUID) -> BirthSupplementState:
        return BirthSupplementState(
            profile_id=profile,
            profile_level=3,
            time_precision="approximate",
            birth_time_mode=BirthTimeMode.APPROX_WINDOW,
            approx_window=None,
            place_display_name="Synthetic",
            timezone_id=_ZONE,
        )

    async def missing(guest_id: UUID) -> BirthSupplementState:
        raise BirthProfileNotFound

    object.__setattr__(birth, "supplement_state", state)
    assert asyncio.run(birth.birth_timezone(guest, profile)) == _ZONE
    assert asyncio.run(birth.birth_timezone(guest, UUID(int=99))) is None
    object.__setattr__(birth, "supplement_state", missing)
    assert asyncio.run(birth.birth_timezone(guest, profile)) is None
