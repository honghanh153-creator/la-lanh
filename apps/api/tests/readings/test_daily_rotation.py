"""B3-1a / A1: per-person Daily rotation (US-21 AC01, AC02, AC04, AC05)."""

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from typing import Any
from uuid import UUID

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput, DateOnlySunResult, NatalChart
from app.domains.readings import daily_psychology
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.daily_personalization import SupportedSituation
from app.domains.readings.daily_psychology import (
    DAILY_ISSUES,
    DAILY_PSYCHOLOGY_MATRIX_VERSION,
    _pick,
    _situation_pool,
)
from app.domains.readings.daily_rotation import (
    DAILY_TOP_K,
    VARIETY_KEY_VERSION,
    axis_slot,
    cycle_order,
    daily_variety_seed,
    day_index,
    derive_variety_key,
    top_k_slot,
)
from app.domains.readings.models import (
    DailyVariety,
    ReadingPlan,
    ReadingProjection,
    ReadingProjectionRecord,
    ReadingPurpose,
    canonical_reading_plan_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_application import (
    MemoryReadingRepository,
    _date_only_snapshot,
    _exact_snapshot,
)

KEY = derive_variety_key(b"test-only-server-secret")
OWNER_A = UUID("30000000-0000-4000-8000-0000000000a1")
OWNER_B = UUID("30000000-0000-4000-8000-0000000000b2")
GUEST = UUID("20000000-0000-4000-8000-0000000000a1")
START = date(2026, 10, 20)


def _variety(owner: UUID, local_date: date, recent: tuple[str, ...] = ()) -> DailyVariety:
    return DailyVariety(
        key_version=VARIETY_KEY_VERSION,
        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
        seed=daily_variety_seed(KEY, owner, DAILY_PSYCHOLOGY_MATRIX_VERSION),
        day_index=day_index(local_date),
        recent_issue_keys=recent,
    )


def _at(local_date: date) -> datetime:
    # 09:00 in Ho Chi Minh City on that calendar day.
    return datetime.combine(local_date, time(2), UTC)


# ------------------------------------------------------------------ pure rotation


@pytest.mark.parametrize("size", [2, 3, 6, 8])
def test_every_axis_changes_every_day_including_cycle_boundaries(size: int) -> None:
    seed = daily_variety_seed(KEY, OWNER_A, "catalog-x")
    values = [axis_slot(seed, "scene", size, day) for day in range(size * 120)]

    assert all(a != b for a, b in pairwise(values))
    for start in range(0, len(values), size):
        assert sorted(values[start : start + size]) == list(range(size))


def test_cycles_are_reshuffled_and_a_single_value_axis_stays_put() -> None:
    seed = daily_variety_seed(KEY, OWNER_A, "catalog-x")

    assert len({cycle_order(seed, "action", cycle, 8) for cycle in range(12)}) > 1
    assert {axis_slot(seed, "action", 1, day) for day in range(30)} == {0}
    with pytest.raises(ValueError):
        axis_slot(seed, "action", 8, -1)


def test_seed_has_no_date_and_separates_owner_catalog_and_key_version() -> None:
    seed = daily_variety_seed(KEY, OWNER_A, "catalog-x")

    assert seed == daily_variety_seed(KEY, OWNER_A, "catalog-x")
    assert seed != daily_variety_seed(KEY, OWNER_B, "catalog-x")
    assert seed != daily_variety_seed(KEY, OWNER_A, "catalog-y")
    assert seed != daily_variety_seed(
        derive_variety_key(b"test-only-server-secret", 2), OWNER_A, "catalog-x"
    )
    assert derive_variety_key(b"test-only-server-secret") != b"test-only-server-secret"
    with pytest.raises(ValueError):
        derive_variety_key(b"secret", 0)


def test_day_index_counts_calendar_days_from_the_epoch() -> None:
    assert day_index(date(2026, 1, 1)) == 0
    assert day_index(date(2026, 10, 20)) == 292
    assert [top_k_slot(day, 5) for day in range(6)] == [0, 1, 2, 0, 1, 2]
    assert [top_k_slot(day, 2) for day in range(4)] == [0, 1, 0, 1]
    assert top_k_slot(7, 1) == 0
    assert DAILY_TOP_K == 3


# ------------------------------------------------------------------ top-K and guard


def _situation(issue_key: str, rank: tuple[int, int, int], rule: str = "r") -> SupportedSituation:
    return SupportedSituation(
        issue_key=issue_key,
        meaning="m",
        factor_refs=(),
        rule_key=f"{rule}-{issue_key}",
        rank=rank,
    )


def _date_only_plan(variety: DailyVariety | None) -> ReadingPlan:
    snapshot = _date_only_snapshot(GUEST, OWNER_A)
    return ReadingPlanner().plan(
        snapshot.result,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
        daily_variety=variety,
    )


def test_top_k_keeps_the_strongest_rule_of_each_issue_then_ranks_by_score() -> None:
    issues = [issue.key for issue in DAILY_ISSUES][:5]
    situations = (
        _situation(issues[0], (1, 0, 0)),
        _situation(issues[1], (3, 0, 0)),
        _situation(issues[1], (2, 0, 0), rule="weaker"),
        _situation(issues[2], (2, 0, 0)),
        _situation(issues[3], (2, 0, 0)),
        _situation(issues[4], (0, 0, 0)),
    )
    plan = _date_only_plan(_variety(OWNER_A, START))

    pool = _situation_pool(plan, situations)

    assert [s.issue_key for s in pool] == [issues[1], *sorted(issues[2:4])]
    assert pool[0].rule_key == f"r-{issues[1]}"
    # Without the rotation the legacy pool (best-rank ties only) is unchanged.
    legacy = _situation_pool(_date_only_plan(None), situations)
    assert [s.issue_key for s in legacy] == [issues[1]]


def test_top_k_rotates_by_day_and_never_serves_a_third_day_in_a_row() -> None:
    a, b, c = (issue.key for issue in DAILY_ISSUES[:3])
    pool = [_situation(a, (1, 0, 0)), _situation(b, (1, 0, 0)), _situation(c, (1, 0, 0))]
    base = _date_only_plan(_variety(OWNER_A, START))
    nominal_day = next(d for d in range(3) if top_k_slot(day_index(START) + d, 3) == 0)
    on_a = START + timedelta(days=nominal_day)

    def plan_for(day: date, recent: tuple[str, ...]) -> ReadingPlan:
        return base.model_copy(update={"daily_variety": _variety(OWNER_A, day, recent)})

    assert _pick(plan_for(on_a, ()), pool).issue_key == a  # type: ignore[union-attr]
    assert _pick(plan_for(on_a, (a,)), pool).issue_key == a  # type: ignore[union-attr]
    assert _pick(plan_for(on_a, (b, a)), pool).issue_key == a  # type: ignore[union-attr]
    assert _pick(plan_for(on_a, (a, a)), pool).issue_key == b  # type: ignore[union-attr]
    # A pool of one stays put: the axes still rotate (tested below).
    assert _pick(plan_for(on_a, (a, a)), pool[:1]).issue_key == a  # type: ignore[union-attr]


# ------------------------------------------------------------------ rendered notes


Note = dict[str, str]


def _rendered(
    chart: DateOnlySunResult | NatalChart, owner: UUID, days: int, *, transits: bool
) -> list[Note]:
    planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
    engine = NatalChartEngine() if transits else None
    notes: list[Note] = []
    for offset in range(days):
        day = START + timedelta(days=offset)
        recent = tuple(note["issue"] for note in notes[-1:-3:-1])
        transit = (
            engine.calculate_transit_to_natal(chart, datetime.combine(day, time(12), UTC))
            if engine is not None and isinstance(chart, NatalChart)
            else None
        )
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            transits=transit,
            editorial_seed=day.isoformat(),
            daily_variety=_variety(owner, day, recent),
        )
        candidate = renderer.render(plan)
        blueprint = candidate.semantic_blueprint
        assert blueprint is not None
        notes.append(
            {
                "issue": blueprint.mechanism_key.removeprefix("psychology:"),
                "headline": candidate.hook,
                "scene": candidate.manifestation,
                "action": candidate.micro_action,
            }
        )
    return notes


def _assert_axes_change_daily(notes: list[Note]) -> None:
    for before, after in pairwise(notes):
        if before["issue"] == after["issue"]:
            assert before["headline"] != after["headline"]
            assert before["scene"] != after["scene"]
            assert before["action"] != after["action"]


def test_date_only_note_changes_every_axis_daily_and_differs_between_owners() -> None:
    result = _date_only_snapshot(GUEST, OWNER_A).result
    owner_a = _rendered(result, OWNER_A, 48, transits=False)
    owner_b = _rendered(result, OWNER_B, 48, transits=False)

    _assert_axes_change_daily(owner_a)
    _assert_axes_change_daily(owner_b)
    # Same birth date, same days: the salt alone separates the two readers.
    assert sum(a != b for a, b in zip(owner_a, owner_b, strict=True)) >= 40


def test_exact_note_with_transits_changes_every_axis_and_respects_the_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sizes: list[int] = []
    original = daily_psychology._pick

    def recording(plan: ReadingPlan, pool: list[SupportedSituation]) -> SupportedSituation | None:
        sizes.append(len(pool))
        return original(plan, pool)

    monkeypatch.setattr(daily_psychology, "_pick", recording)
    result = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine()).result
    notes = _rendered(result, OWNER_A, 30, transits=True)

    assert len(sizes) == len(notes)  # exact plans pick once, while planning
    _assert_axes_change_daily(notes)
    for day in range(2, len(notes)):
        same = notes[day]["issue"] == notes[day - 1]["issue"] == notes[day - 2]["issue"]
        assert not (same and sizes[day] >= 2)


# Keys computed on the parent commit (8e05e01), before DailyVariety existed.
LEGACY_DATE_ONLY_KEY = "0187125110d5ce9eee40eddfcc59239eaf880571ad5ca9f8a5d96ad66c30bc86"
LEGACY_EXACT_KEY = "7493a6ded8c7574289bfa3078c4957b9a047a614db885d0b178eac171e7ab672"


def test_legacy_plans_keep_their_identity() -> None:
    legacy = _date_only_plan(None)
    engine = NatalChartEngine()
    chart = _exact_snapshot(GUEST, OWNER_A, engine).result
    assert isinstance(chart, NatalChart)
    exact = ReadingPlanner().plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=engine.calculate_transit_to_natal(chart, datetime(2026, 10, 20, 12, tzinfo=UTC)),
        editorial_seed="2026-10-20",
    )
    rotated = _date_only_plan(_variety(OWNER_A, START))

    assert canonical_reading_plan_key(legacy) == LEGACY_DATE_ONLY_KEY
    assert canonical_reading_plan_key(exact) == LEGACY_EXACT_KEY
    assert canonical_reading_plan_key(rotated) != LEGACY_DATE_ONLY_KEY
    assert legacy.plan_hash != rotated.plan_hash
    with pytest.raises(ValueError):
        ReadingPlanner().plan(
            _date_only_snapshot(GUEST, OWNER_A).result,
            purpose=ReadingPurpose.AURA,
            daily_variety=_variety(OWNER_A, START),
        )


# ------------------------------------------------------------------ application


def _service(repository: MemoryReadingRepository, start: date | None) -> ReadingApplicationService:
    return ReadingApplicationService(
        repository,
        NatalChartEngine(),
        daily_variety_key=KEY,
        daily_variety_from=start,
    )


def _stored_plan(repository: MemoryReadingRepository, revision_id: UUID) -> ReadingPlan:
    revision = repository.revisions[(GUEST, OWNER_A, revision_id)]
    return next(r.plan for r in repository.plans.values() if r.id == revision.plan_id)


async def test_rotation_starts_on_the_configured_day_and_leaves_earlier_days_alone() -> None:
    repository = MemoryReadingRepository()
    snapshot = _date_only_snapshot(GUEST, OWNER_A)
    legacy_service = ReadingApplicationService(MemoryReadingRepository(), NatalChartEngine())
    service = _service(repository, START)

    before = await service.project(
        guest_id=GUEST,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=_at(START - timedelta(days=1)),
    )
    legacy = await legacy_service.project(
        guest_id=GUEST,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=_at(START - timedelta(days=1)),
    )
    on_start = await service.project(
        guest_id=GUEST,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=_at(START),
    )

    assert before.active.sections == legacy.active.sections
    assert _stored_plan(repository, before.active.revision_id).daily_variety is None
    variety = _stored_plan(repository, on_start.active.revision_id).daily_variety
    assert variety is not None
    assert variety.day_index == day_index(START)
    assert variety.key_version == VARIETY_KEY_VERSION


async def test_rotation_replays_the_same_revision_after_restart() -> None:
    repository = MemoryReadingRepository()
    snapshot = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine())

    first = await _service(repository, START).project(
        guest_id=GUEST,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=_at(START),
    )
    later_same_day = datetime.combine(START, time(15), UTC)  # 22:00 local, same calendar day
    restarted = await _service(repository, START).project(
        guest_id=GUEST,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=later_same_day,
    )

    assert restarted.active.revision_id == first.active.revision_id
    assert restarted.active.sections == first.active.sections
    assert restarted.available_update is None
    assert len(repository.plans) == 1


async def test_odd_day_guard_equals_what_the_even_day_before_actually_served() -> None:
    """PR #39 review: the guard reads no history, yet an odd day's guard pair is exactly the
    situation served the day before, and every served day is reproduced by recomputation."""

    for snapshot in (_date_only_snapshot(GUEST, OWNER_A), *_snapshots(3)):
        repository = MemoryReadingRepository()
        service = _service(repository, START)
        previous_served: str | None = None
        for offset in range(10):
            day = START + timedelta(days=offset)
            projection = await _open(service, snapshot, day)
            served = _served(repository, projection).semantic_blueprint.mechanism_key
            served = served.removeprefix("psychology:")
            plan = _stored_plan(repository, projection.active.revision_id)
            assert plan.daily_variety is not None
            recent = plan.daily_variety.recent_issue_keys
            assert served == await service._computed_daily_issue(
                OWNER_A, snapshot.result, day, None, recent=recent
            )
            if day_index(day) % 2 == 1 and previous_served is not None:
                assert recent == (previous_served, previous_served)
            previous_served = served
    snapshot = _date_only_snapshot(GUEST, OWNER_A)
    assert (
        await _service(MemoryReadingRepository(), START)._computed_daily_issue(
            OWNER_A, snapshot.result, START - timedelta(days=1), None
        )
        is None
    )


def test_rotation_start_date_is_an_opt_in_setting_not_before_the_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pydantic import ValidationError

    from app.config import Settings

    assert Settings().daily_variety_from is None
    monkeypatch.setenv("LA_LANH_DAILY_VARIETY_FROM", "2026-10-25")
    assert Settings().daily_variety_from == date(2026, 10, 25)
    monkeypatch.setenv("LA_LANH_DAILY_VARIETY_FROM", "2025-12-31")
    with pytest.raises(ValidationError):
        Settings()


def test_rotation_seed_never_reaches_a_provider_payload() -> None:
    import json

    from app.infrastructure.generation.openai import _safe_payload

    plan = _date_only_plan(_variety(OWNER_A, START, ("capacity-before-agreement",)))
    assert plan.daily_variety is not None
    payload = json.dumps(_safe_payload(plan))

    assert plan.daily_variety.seed not in payload
    assert "daily_variety" not in payload
    assert "capacity-before-agreement" not in payload


# ------------------------------------------------------------------ same-day replay (Codex P2)


def _plans_for(repository: MemoryReadingRepository, day: date) -> list[ReadingPlan]:
    return [
        record.plan
        for record in repository.plans.values()
        if record.plan.daily_variety is not None
        and record.plan.daily_variety.day_index == day_index(day)
    ]


async def _open(
    service: ReadingApplicationService, snapshot: object, day: date, hour: int = 2
) -> ReadingProjection:
    return await service.project(
        guest_id=GUEST,
        snapshot=snapshot,  # type: ignore[arg-type]
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=datetime.combine(day, time(hour), UTC),
    )


async def test_late_previous_day_never_changes_an_opened_note() -> None:
    repository = MemoryReadingRepository()
    snapshot = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine())
    service = _service(repository, START)
    d2, d1, d0 = START, START + timedelta(days=1), START + timedelta(days=2)

    await _open(service, snapshot, d2)
    first = await _open(service, snapshot, d0)  # D-1 still in flight: the guard ignores it
    await _open(service, snapshot, d1)  # D-1 completes after D was first opened
    reopened = await _open(service, snapshot, d0, hour=15)

    assert reopened.active.revision_id == first.active.revision_id
    assert reopened.active.sections == first.active.sections
    assert reopened.available_update is None
    plans = _plans_for(repository, d0)
    assert len(plans) == 1
    assert plans[0].daily_variety is not None
    # The guard reads no history, so a late D-1 cannot change what D chose.
    expected = await service._guard_issue_keys(OWNER_A, snapshot.result, d0, None)
    assert plans[0].daily_variety.recent_issue_keys == expected


async def test_new_key_material_after_restart_only_applies_to_new_days() -> None:
    repository = MemoryReadingRepository()
    snapshot = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine())
    other_key = derive_variety_key(b"another-test-only-secret")

    first = await _open(_service(repository, START), snapshot, START)
    restarted = ReadingApplicationService(
        repository, NatalChartEngine(), daily_variety_key=other_key, daily_variety_from=START
    )
    same_day = await _open(restarted, snapshot, START, hour=15)
    await _open(restarted, snapshot, START + timedelta(days=1))

    assert same_day.active.revision_id == first.active.revision_id
    assert same_day.available_update is None
    assert len(_plans_for(repository, START)) == 1
    (tomorrow,) = _plans_for(repository, START + timedelta(days=1))
    assert tomorrow.daily_variety is not None
    assert tomorrow.daily_variety.seed == daily_variety_seed(
        other_key, OWNER_A, DAILY_PSYCHOLOGY_MATRIX_VERSION
    )


class _GatedRepository(MemoryReadingRepository):
    """Holds the first request for one scope inside get_or_create_projection."""

    def __init__(self) -> None:
        super().__init__()
        self.held_scope: str | None = None
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def get_or_create_projection(
        self, record: ReadingProjectionRecord
    ) -> tuple[ReadingProjectionRecord, bool]:
        if record.scope_key == self.held_scope:
            self.held_scope = None
            self.entered.set()
            await self.release.wait()
        return await super().get_or_create_projection(record)


async def test_concurrent_first_readings_keep_the_first_writer() -> None:
    repository = _GatedRepository()
    snapshot = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine())
    service = _service(repository, START)
    d2, d1, d0 = START, START + timedelta(days=1), START + timedelta(days=2)
    await _open(service, snapshot, d2)
    first_of_d0 = await _open(_service(MemoryReadingRepository(), START), snapshot, d0)
    repository.held_scope = first_of_d0.scope_key

    # Request A reads an empty history, then stalls before touching the projection.
    slow = asyncio.create_task(_open(service, snapshot, d0))
    await repository.entered.wait()
    # Meanwhile D-1 completes and request B creates and activates D with a full history.
    await _open(service, snapshot, d1)
    fast = await _open(service, snapshot, d0, hour=3)
    repository.release.set()
    late = await slow

    # Both requests chose before either stored. The guard reads no history, so both chose the
    # same plan (stored once by key); the first writer still wins.
    assert len(_plans_for(repository, d0)) == 1
    assert late.active.revision_id == fast.active.revision_id
    assert late.active.sections == fast.active.sections
    assert late.available_update is None
    again = await _open(service, snapshot, d0, hour=15)
    assert again.active.revision_id == fast.active.revision_id
    assert again.available_update is None


async def test_start_date_set_after_today_was_opened_keeps_today() -> None:
    repository = MemoryReadingRepository()
    snapshot = _exact_snapshot(GUEST, OWNER_A, NatalChartEngine())
    legacy = ReadingApplicationService(repository, NatalChartEngine())

    opened = await _open(legacy, snapshot, START)
    for start in (START + timedelta(days=1), START):  # FROM = tomorrow, then even FROM = today
        again = await _open(_service(repository, start), snapshot, START, hour=15)
        assert again.active.revision_id == opened.active.revision_id
        assert again.available_update is None
    assert _plans_for(repository, START) == []


async def test_catalog_or_chart_change_is_still_an_intentional_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.domains.readings.application as application

    repository = MemoryReadingRepository()
    engine = NatalChartEngine()
    snapshot = _exact_snapshot(GUEST, OWNER_A, engine)
    service = _service(repository, START)
    opened = await _open(service, snapshot, START)

    monkeypatch.setattr(application, "DAILY_PSYCHOLOGY_MATRIX_VERSION", "catalog-next")
    bumped = await _open(service, snapshot, START, hour=15)
    assert bumped.active.revision_id == opened.active.revision_id
    assert bumped.available_update is not None
    monkeypatch.undo()

    repository = MemoryReadingRepository()
    service = _service(repository, START)
    opened = await _open(service, snapshot, START)
    edited = replace(snapshot, id=UUID("10000000-0000-4000-8000-0000000000ed"))
    changed = await _open(service, edited, START, hour=15)
    assert changed.active.revision_id == opened.active.revision_id
    assert changed.available_update is not None


class _FlakyTransitEngine(NatalChartEngine):
    """Transit calculation fails while ``failing`` is set (the service falls back to natal)."""

    failing = False

    def calculate_transit_to_natal(self, *args: Any, **kwargs: Any) -> Any:
        if self.failing:
            raise RuntimeError("synthetic transient transit failure")
        return super().calculate_transit_to_natal(*args, **kwargs)


# A day on which this synthetic chart's situation is driven by a transit, so the
# natal-only fallback and the transit plan differ.
TRANSIT_DAY = date(2026, 10, 22)


def _transit_refs(plan: ReadingPlan) -> set[str]:
    return {factor.id for factor in plan.factors if factor.source.value == "transit"}


async def test_natal_fallback_loser_replays_the_transit_winner() -> None:
    repository = _GatedRepository()
    engine = _FlakyTransitEngine()
    snapshot = _exact_snapshot(GUEST, OWNER_A, engine)
    service = ReadingApplicationService(
        repository, engine, daily_variety_key=KEY, daily_variety_from=START
    )
    probe = await _open(_service(MemoryReadingRepository(), START), snapshot, TRANSIT_DAY)
    repository.held_scope = probe.scope_key

    engine.failing = True  # request A falls back to a natal-only plan, then stalls
    slow = asyncio.create_task(_open(service, snapshot, TRANSIT_DAY))
    await repository.entered.wait()
    engine.failing = False  # request B computes transits and activates first
    fast = await _open(service, snapshot, TRANSIT_DAY, hour=3)
    repository.release.set()
    late = await slow
    healthy = await _open(service, snapshot, TRANSIT_DAY, hour=15)

    plans = _plans_for(repository, TRANSIT_DAY)
    assert len(plans) == 2
    assert {bool(_transit_refs(plan)) for plan in plans} == {True, False}
    for projection in (late, healthy):
        assert projection.active.revision_id == fast.active.revision_id
        assert projection.active.sections == fast.active.sections
        assert projection.available_update is None


async def test_note_opened_during_a_transit_outage_replays_after_recovery() -> None:
    repository = MemoryReadingRepository()
    engine = _FlakyTransitEngine()
    snapshot = _exact_snapshot(GUEST, OWNER_A, engine)
    service = ReadingApplicationService(
        repository, engine, daily_variety_key=KEY, daily_variety_from=START
    )

    engine.failing = True
    outage = await _open(service, snapshot, TRANSIT_DAY)
    engine.failing = False
    recovered = await _open(service, snapshot, TRANSIT_DAY, hour=15)
    tomorrow = await _open(service, snapshot, TRANSIT_DAY + timedelta(days=1))

    (today_plan,) = _plans_for(repository, TRANSIT_DAY)
    assert _transit_refs(today_plan) == set()
    healthy = await _open(_service(MemoryReadingRepository(), START), snapshot, TRANSIT_DAY)
    assert healthy.active.sections != outage.active.sections  # recovery alone would differ
    assert recovered.active.revision_id == outage.active.revision_id
    assert recovered.active.sections == outage.active.sections
    assert recovered.available_update is None
    # The engine is healthy again for a new day.
    (tomorrow_plan,) = _plans_for(repository, TRANSIT_DAY + timedelta(days=1))
    assert tomorrow.active.revision_id != outage.active.revision_id
    assert tomorrow_plan.daily_variety is not None


def _snapshots(count: int) -> list[Any]:
    """Synthetic exact charts with different birth times; nothing real."""

    engine = NatalChartEngine()
    base = _exact_snapshot(GUEST, OWNER_A, engine)
    snapshots = []
    for index in range(count):
        chart = engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(
                    1980 + index, 1 + index % 12, 1 + (7 * index) % 28, (5 * index) % 24, tzinfo=UTC
                ),
                latitude=10.8231 + index % 12,
                longitude=106.6297,
            )
        )
        snapshots.append(replace(base, result=chart))
    return snapshots


def _served(repository: MemoryReadingRepository, projection: ReadingProjection) -> Any:
    revision = repository.revisions[(GUEST, OWNER_A, projection.active.revision_id)]
    candidate = revision.evaluation.publishable_candidate
    assert candidate is not None and candidate.semantic_blueprint is not None
    return candidate


async def test_recomputed_situation_matches_what_was_served() -> None:
    """Opening each day with nothing stored gives the same note as a continuous history: the
    guard depends on the chart and date only."""

    for snapshot in _snapshots(4):
        continuous = MemoryReadingRepository()
        service = _service(continuous, START)
        for offset in range(8):
            day = START + timedelta(days=offset)
            kept = _served(continuous, await _open(service, snapshot, day))
            fresh_repository = MemoryReadingRepository()
            fresh = _served(
                fresh_repository, await _open(_service(fresh_repository, START), snapshot, day)
            )
            assert kept.semantic_blueprint.mechanism_key == fresh.semantic_blueprint.mechanism_key
            assert (kept.hook, kept.manifestation, kept.micro_action) == (
                fresh.hook,
                fresh.manifestation,
                fresh.micro_action,
            )


async def test_consecutive_notes_without_history_stay_at_most_60_percent_similar() -> None:
    """Owner rule 2026-10-21: if two consecutive notes would be more than 60% alike, write a
    different angle. Each day here is opened with no stored history (as after the 24-hour
    window); the guard reads no history. Axes: situation, title, scene, action, transit."""

    worst = 0.0
    for snapshot in _snapshots(4):
        previous: tuple[object, ...] | None = None
        situations: list[object] = []
        for offset in range(14):
            repository = MemoryReadingRepository()  # nothing kept from earlier days
            projection = await _open(
                _service(repository, START), snapshot, START + timedelta(days=offset)
            )
            candidate = _served(repository, projection)
            axes = (
                candidate.semantic_blueprint.mechanism_key,
                candidate.hook,
                candidate.manifestation,
                candidate.micro_action,
                candidate.transit,
            )
            if previous is not None:
                similarity = sum(a == b for a, b in zip(axes, previous, strict=True)) / len(axes)
                worst = max(worst, similarity)
                assert similarity <= 0.6, (offset, similarity)
            previous = axes
            situations.append(axes[0])
        # AC05 holds again without history: no situation three calendar days in a row.
        runs = zip(situations, situations[1:], situations[2:], strict=False)
        assert not any(a == b == c for a, b, c in runs)
    assert worst > 0  # the measure is exercised (some axis can repeat, e.g. the situation)


async def _served_issue_without_history(snapshot: Any, day: date) -> tuple[str, int]:
    """(served situation, day index) for ``day`` opened with nothing stored before it."""

    repository = MemoryReadingRepository()
    projection = await _open(_service(repository, START), snapshot, day)
    key = _served(repository, projection).semantic_blueprint.mechanism_key
    return key.removeprefix("psychology:"), day_index(day)


async def test_codex_counterexample_no_longer_serves_three_days_in_a_row() -> None:
    """PR #39 review counterexample: 2027-04-22..24 all served group-pressure (pools 2/2/3)
    because recomputing D-2 dropped that day's guard move. Final output must differ."""

    engine = NatalChartEngine()
    snapshot = replace(
        _exact_snapshot(GUEST, OWNER_A, engine),
        result=engine.calculate_chart(
            ChartInput(
                utc_datetime=datetime(1993, 2, 8, 17, tzinfo=UTC),
                latitude=11.8231,
                longitude=106.6297,
            )
        ),
    )
    issues = [
        (await _served_issue_without_history(snapshot, date(2027, 4, day)))[0]
        for day in range(20, 25)
    ]
    assert not any(a == b == c for a, b, c in zip(issues, issues[1:], issues[2:], strict=False))


async def test_census_no_situation_three_days_in_a_row_on_actual_output() -> None:
    """AC05 on what is actually served, with no stored history, across many synthetic charts
    and two months, including guard moves followed by changing pools. A situation may repeat a
    third day only when that third day has a one-entry pool (the AC05 exemption)."""

    moved = moved_then_changed = exempt = 0
    for snapshot in _snapshots(24):
        service = _service(MemoryReadingRepository(), START)
        served: list[str] = []
        nominal: list[str | None] = []
        for offset in range(60):
            day = START + timedelta(days=offset)
            issue, _ = await _served_issue_without_history(snapshot, day)
            served.append(issue)
            nominal.append(await service._computed_daily_issue(OWNER_A, snapshot.result, day, None))
            if issue != nominal[-1]:
                moved += 1
            if offset >= 1 and served[-2] != nominal[-2] and nominal[-1] != nominal[-2]:
                moved_then_changed += 1
            if offset >= 2 and served[-1] == served[-2] == served[-3]:
                # Only a one-entry pool on the third day may keep it: moving must be impossible.
                stuck = await service._computed_daily_issue(
                    OWNER_A, snapshot.result, day, None, recent=(issue, issue)
                )
                assert stuck == issue, (day, served[-3:])
                exempt += 1
    assert moved > 0 and moved_then_changed > 0  # the guard and changing pools are exercised
    # `exempt` counts third days whose one-entry pool made moving impossible (6 of 1440 days
    # in this census at the time of writing); each was verified above.
