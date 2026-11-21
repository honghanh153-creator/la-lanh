"""Daily step 2 wiring: an approximate Daily may carry a transit proven over the birth window.

Synthetic charts only (a fixed 1994 instant read as an approximate window); no real data.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, cast
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
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    BackgroundLens,
    DailyTransitRole,
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
_LENSES = tuple(lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO)


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


def test_a_lens_never_changes_the_factors_or_the_evidence_of_a_window_daily() -> None:
    """US-03 AC22 with a transit (Codex r1 on #726). The day's transit is chosen once, without
    the lens, and every lens keeps it: the factors, the rendered evidence, the precision and the
    transit proof are equal for every lens. A lens changes only the scene and the action, and
    the "why today" sentence is shown only when the kept transit explains the lens's scene."""

    chart = _approximate()
    renderer = DeterministicVietnameseRenderer()
    lenses = tuple(lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO)
    kept_without_reason = 0
    scenes_changed = 0
    for person in range(3):
        for day in _DAYS:
            plain = _plan(chart, day, person)
            plain_card = renderer.render(plain)
            assert evaluate_candidate(plain, plain_card).accepted
            for lens in lenses:
                framed = _plan(chart, day, person, lens)
                assert framed.precision is plain.precision is TimePrecision.APPROXIMATE
                assert framed.factors == plain.factors
                assert framed.hero_factor_refs == plain.hero_factor_refs
                assert framed.transit_policy == plain.transit_policy
                card = renderer.render(framed)
                assert card.evidence == plain_card.evidence
                assert evaluate_candidate(framed, card).accepted
                selection = framed.daily_selection
                assert selection is not None
                # The reason sentence exists exactly when the kept transit explains this scene.
                held = [f for f in framed.factors if f.source is FactorSource.TRANSIT]
                withheld = framed.transit_reason_withheld is True
                assert (card.transit is not None) == (bool(held) and not withheld)
                assert not withheld or held
                kept_without_reason += withheld
                scenes_changed += card.manifestation != plain_card.manifestation
    assert scenes_changed, "a lens still changes the scene"
    assert kept_without_reason, "some lens keeps the day's transit as evidence only"


def _served_plans(
    person: int, days: list[date]
) -> dict[tuple[date, BackgroundLens | None], ReadingPlan]:
    """Every lens of every day, opened through the reading service with the rotation on."""

    import asyncio

    from app.domains.birth.models import BirthSnapshotRecord
    from app.domains.readings.application import ReadingApplicationService
    from tests.readings.test_application import MemoryReadingRepository

    guest, profile = UUID(int=900 + person), UUID(int=person + 1)

    async def zone(guest_id: UUID, profile_id: UUID) -> str | None:
        return _ZONE

    repository = MemoryReadingRepository()
    service = ReadingApplicationService(
        cast(Any, repository),
        _ENGINE,
        daily_variety_key=_KEY,
        daily_variety_from=date(2026, 10, 20),
        birth_timezone_lookup=zone,
    )
    snapshot = BirthSnapshotRecord(
        id=UUID(int=700 + person),
        guest_id=guest,
        profile_id=profile,
        input_hash=b"approximate",
        birth_date_ciphertext="encrypted",
        result=_approximate(),
        created_at=datetime(2026, 9, 7, 4, 30, tzinfo=UTC),
    )

    async def run() -> dict[tuple[date, BackgroundLens | None], ReadingPlan]:
        served: dict[tuple[date, BackgroundLens | None], ReadingPlan] = {}
        for day in days:
            for lens in (None, *_LENSES):
                projection = await service.project(
                    guest_id=guest,
                    snapshot=snapshot,
                    purpose=ReadingPurpose.DAILY_NOTE,
                    requested_at=datetime.combine(day, time(12), tzinfo=UTC),
                    background_lens=lens,
                )
                revision = repository.revisions[(guest, profile, projection.active.revision_id)]
                served[(day, lens)] = next(
                    r.plan for r in repository.plans.values() if r.id == revision.plan_id
                )
        return served

    return asyncio.run(run())


def test_serving_keeps_the_factors_and_evidence_of_a_window_daily_for_every_lens() -> None:
    """US-03 AC22 on the serving path (Codex r2 on #726). The service gives every lens its own
    rotation guard pair; that pair may move the lens's scene but never the day's transit. The
    r2 counterexample (profile 1, 2026-11-02, Relationships) is inside this range."""

    renderer = DeterministicVietnameseRenderer()
    days = _DAYS
    guards_differ = 0
    with_transit = 0
    for person in range(3):
        served = _served_plans(person, days)
        for day in days:
            plain = served[(day, None)]
            plain_card = renderer.render(plain)
            with_transit += any(f.source is FactorSource.TRANSIT for f in plain.factors)
            for lens in _LENSES:
                framed = served[(day, lens)]
                assert framed.daily_variety is not None and plain.daily_variety is not None
                guards_differ += (
                    framed.daily_variety.recent_issue_keys != plain.daily_variety.recent_issue_keys
                )
                assert framed.factors == plain.factors, (person, day, lens)
                assert framed.transit_policy == plain.transit_policy
                assert framed.precision is plain.precision
                card = renderer.render(framed)
                assert card.evidence == plain_card.evidence, (person, day, lens)
                assert evaluate_candidate(framed, card).accepted
    assert guards_differ, "the range holds days where a lens has its own guard pair"
    assert with_transit, "the range holds days with a proven transit"


def test_the_transit_choice_ignores_the_rotation_guard_pair() -> None:
    chart = _approximate()
    for person in range(3):
        for day in _DAYS:
            plain = _plan(chart, day, person)
            assert plain.daily_selection is not None
            issue = plain.daily_selection.issue_key
            guarded = ReadingPlanner().plan(
                chart,
                purpose=ReadingPurpose.DAILY_NOTE,
                transits=interval_transit_to_natal(
                    _ENGINE, chart, datetime.combine(day, time(5), tzinfo=UTC), birth_timezone=_ZONE
                ),
                editorial_seed=day.isoformat(),
                daily_variety=_variety(person, day).model_copy(
                    update={"recent_issue_keys": (issue, issue)}
                ),
            )
            assert guarded.factors == plain.factors, (person, day)


def _reads_before_step_2(plan: ReadingPlan) -> bool:
    """The plan rule of every reader before Daily step 2 (base 328073b, models.py): a selected
    Daily plan holds exactly its chosen transit, and a transit has a role."""

    selection = plan.daily_selection
    assert selection is not None
    transit_ids = {f.id for f in plan.factors if f.source is FactorSource.TRANSIT}
    return transit_ids == ({selection.transit_ref} if selection.transit_ref else set()) and (
        (selection.transit_ref is None) == (selection.transit_role is DailyTransitRole.NONE)
    )


def test_every_window_plan_stays_readable_by_the_reader_before_step_2() -> None:
    """G4 rollback (Codex r2 on #726). A stored plan must load under the previous release, so a
    transit kept as evidence only is stored in the old shape (reference and role) and marked
    with a field old readers ignore. The old gate then rejects its reason and the old service
    plans the day again from the natal chart."""

    chart = _approximate()
    evidence_only = 0
    for person in range(3):
        for day in _DAYS:
            for lens in (None, *_LENSES):
                plan = _plan(chart, day, person, lens)
                assert _reads_before_step_2(plan), (person, day, lens)
                evidence_only += plan.transit_reason_withheld is True
    assert evidence_only, "the range holds plans that keep the transit as evidence only"


def test_a_withheld_reason_is_allowed_only_on_a_window_plan_with_its_transit() -> None:
    plan = next(
        plan
        for person in range(3)
        for day in _DAYS
        for lens in _LENSES
        if (plan := _plan(_approximate(), day, person, lens)).transit_reason_withheld
    )
    assert DeterministicVietnameseRenderer().render(plan).transit is None
    data = plan.model_dump()
    with pytest.raises(ValidationError):
        ReadingPlan.model_validate({**data, "transit_policy": None})
    natal = [f for f in data["factors"] if f["source"] != FactorSource.TRANSIT.value]
    with pytest.raises(ValidationError):
        ReadingPlan.model_validate({**data, "factors": natal})
    # Marked and unmarked plans are different plans.
    assert canonical_reading_plan_key(plan) != canonical_reading_plan_key(
        plan.model_copy(update={"transit_reason_withheld": None})
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


# --- US-03 AC22 when something fails for one request only (Codex r3 on #726) -----------------


def _transit_day(person: int) -> date:
    """A day on which this synthetic person's Daily holds a proven transit."""

    chart = _approximate()
    return next(
        day
        for day in _DAYS
        if any(f.source is FactorSource.TRANSIT for f in _plan(chart, day, person).factors)
    )


class _Desk:
    """One synthetic owner's reading service, with a zone lookup the test can break."""

    def __init__(self, person: int) -> None:
        from app.domains.birth.models import BirthSnapshotRecord
        from app.domains.readings.application import ReadingApplicationService
        from tests.readings.test_application import MemoryReadingRepository

        self.guest, self.profile = UUID(int=900 + person), UUID(int=person + 1)
        self.zone_fails = False
        self.repository = MemoryReadingRepository()
        self.service = ReadingApplicationService(
            cast(Any, self.repository),
            _ENGINE,
            daily_variety_key=_KEY,
            daily_variety_from=date(2026, 10, 20),
            birth_timezone_lookup=self._zone,
        )
        self.snapshot = BirthSnapshotRecord(
            id=UUID(int=700 + person),
            guest_id=self.guest,
            profile_id=self.profile,
            input_hash=b"approximate",
            birth_date_ciphertext="encrypted",
            result=_approximate(),
            created_at=datetime(2026, 9, 7, 4, 30, tzinfo=UTC),
        )

    async def _zone(self, guest_id: UUID, profile_id: UUID) -> str | None:
        if self.zone_fails:
            raise RuntimeError("store unavailable")
        return _ZONE

    def open(self, day: date, lens: BackgroundLens | None) -> ReadingPlan:
        import asyncio

        projection = asyncio.run(
            self.service.project(
                guest_id=self.guest,
                snapshot=self.snapshot,
                purpose=ReadingPurpose.DAILY_NOTE,
                requested_at=datetime.combine(day, time(12), tzinfo=UTC),
                background_lens=lens,
            )
        )
        key = (self.guest, self.profile, projection.active.revision_id)
        plan_id = self.repository.revisions[key].plan_id
        return next(r.plan for r in self.repository.plans.values() if r.id == plan_id)


def _same_evidence(first: ReadingPlan, other: ReadingPlan) -> None:
    renderer = DeterministicVietnameseRenderer()
    assert other.factors == first.factors
    assert other.transit_policy == first.transit_policy
    assert other.precision is first.precision
    card = renderer.render(other)
    assert card.evidence == renderer.render(first).evidence
    assert evaluate_candidate(other, card).accepted


def _broken_calculation(*args: object, **kwargs: object) -> None:
    raise RuntimeError("ephemeris unavailable")


def test_a_failed_calculation_for_the_first_lens_holds_for_every_lens_of_the_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The r3 counterexample: the calculation fails while the first lens is opened and works
    again for the next. The first lens was served from the natal chart, so the day stays so."""

    from app.domains.readings import application

    desk = _Desk(0)
    day = _transit_day(0)
    monkeypatch.setattr(application, "interval_transit_to_natal", _broken_calculation)
    first = desk.open(day, None)
    assert not any(f.source is FactorSource.TRANSIT for f in first.factors)
    monkeypatch.setattr(application, "interval_transit_to_natal", interval_transit_to_natal)
    for lens in _LENSES:
        _same_evidence(first, desk.open(day, lens))
    _same_evidence(first, desk.open(day, None))
    # The next day is decided again, on its own.
    assert any(
        f.source is FactorSource.TRANSIT
        for later in _DAYS
        if later > day
        for f in desk.open(later, None).factors
    )


def test_a_failed_calculation_for_a_later_lens_keeps_the_transit_of_the_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.domains.readings import application

    desk = _Desk(1)
    day = _transit_day(1)
    first = desk.open(day, None)
    assert any(f.source is FactorSource.TRANSIT for f in first.factors)
    monkeypatch.setattr(application, "interval_transit_to_natal", _broken_calculation)
    for lens in _LENSES:
        _same_evidence(first, desk.open(day, lens))


def test_a_failed_zone_lookup_for_one_lens_never_splits_the_evidence_of_the_day() -> None:
    """Without the zone the wide window applies and fewer contacts qualify. Whichever lens is
    opened first decides; a lookup that fails or recovers later changes nothing that day."""

    for person in range(3):
        for fails_first in (True, False):
            desk = _Desk(person)
            for day in _DAYS[:10]:
                desk.zone_fails = fails_first
                first = desk.open(day, _LENSES[0])
                desk.zone_fails = not fails_first
                for lens in (None, *_LENSES[1:]):
                    _same_evidence(first, desk.open(day, lens))


def test_a_rejected_reason_keeps_the_transit_as_evidence_for_that_lens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B1b on a window Daily: when a gate rejects a lens's reason sentence, the lens loses the
    sentence, not the day's transit evidence."""

    from app.domains.readings import application
    from app.domains.readings.models import (
        CandidateEvaluation,
        GateFailureCode,
        ReadingCandidate,
    )

    rejected: list[BackgroundLens | None] = []

    def strict(plan: ReadingPlan, candidate: ReadingCandidate) -> CandidateEvaluation:
        evaluation = evaluate_candidate(plan, candidate)
        if candidate.transit is None or plan.background_lens is None:
            return evaluation
        rejected.append(plan.background_lens)
        failed = evaluation.reports[0].model_copy(
            update={
                "passed": False,
                "failure_codes": (GateFailureCode.EVIDENCE_DAILY_TRANSIT_LINK,),
            }
        )
        return CandidateEvaluation(accepted=False, reports=(failed, *evaluation.reports[1:]))

    monkeypatch.setattr(application, "evaluate_candidate", strict)
    for person in range(3):
        desk = _Desk(person)
        day = _transit_day(person)
        first = desk.open(day, None)
        assert any(f.source is FactorSource.TRANSIT for f in first.factors)
        for lens in _LENSES:
            framed = desk.open(day, lens)
            _same_evidence(first, framed)
            assert framed.transit_reason_withheld is True
    assert rejected, "some lens had its reason sentence rejected"


def test_the_planner_repeats_a_day_transit_and_can_withhold_its_reason() -> None:
    from app.domains.readings.planner import DayTransit

    chart = _approximate()
    day = _transit_day(0)
    plain = _plan(chart, day)
    transit = next(f for f in plain.factors if f.source is FactorSource.TRANSIT)

    def repeat(
        decision: DayTransit, lens: BackgroundLens | None, withhold: bool = False
    ) -> ReadingPlan:
        return ReadingPlanner().plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed=day.isoformat(),
            daily_variety=_variety(0, day),
            background_lens=lens,
            day_transit=decision,
            withhold_transit_reason=withhold,
        )

    for lens in (None, *_LENSES):
        assert repeat(DayTransit(transit, plain.transit_policy), lens) == _plan(chart, day, 0, lens)
        natal = repeat(DayTransit(None, None), lens)
        assert not any(f.source is FactorSource.TRANSIT for f in natal.factors)
        assert natal.transit_policy is None and natal.transit_reason_withheld is None
        withheld = repeat(DayTransit(transit, plain.transit_policy), lens, withhold=True)
        assert withheld.factors == plain.factors and withheld.transit_reason_withheld is True
        assert _reads_before_step_2(withheld)
        assert DeterministicVietnameseRenderer().render(withheld).transit is None
    # A transit whose natal placement the chart no longer offers is not carried over.
    stray = transit.model_copy(update={"child_refs": ("natal:unknown",)})
    assert not any(
        f.source is FactorSource.TRANSIT
        for f in repeat(DayTransit(stray, plain.transit_policy), None).factors
    )
