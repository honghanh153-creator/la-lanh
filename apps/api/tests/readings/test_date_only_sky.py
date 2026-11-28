"""Date-only sky (#841 follow-up, US-21 AC07): today's whole-sign contacts to the Sun sign."""

from __future__ import annotations

from datetime import date, timedelta
from itertools import pairwise
from typing import Any

import pytest

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, BodyPosition, DateOnlySunResult, ZodiacSign
from app.domains.readings import daily_psychology
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.daily_personalization import (
    SupportedSituation,
    eligible_daily_situations,
)
from app.domains.readings.daily_psychology import DAILY_PSYCHOLOGY_MATRIX_VERSION
from app.domains.readings.daily_rotation import VARIETY_KEY_VERSION, day_index
from app.domains.readings.date_only_sky import sky_contacts
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import DailyVariety, ReadingPlan, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from tests.readings.test_application import MemoryReadingRepository, _date_only_snapshot
from tests.readings.test_daily_rotation import GUEST, KEY, OWNER_A, _open, _served, _stored_plan

START = date(2026, 11, 21)


def _at(body: str, sign: ZodiacSign) -> BodyPosition:
    return BodyPosition(
        body=BodyName(body),
        longitude=float(list(ZodiacSign).index(sign) * 30 + 15),
        latitude=0.0,
        distance_au=1.0,
        longitude_speed=1.0,
        retrograde=False,
        sign=sign,
        degree_in_sign=15.0,
    )


def test_whole_sign_contacts_hold_only_for_bodies_in_one_sign_all_day() -> None:
    start = [
        _at("saturn", ZodiacSign.GEMINI),  # square from pisces
        _at("jupiter", ZodiacSign.CANCER),  # trine
        _at("mars", ZodiacSign.PISCES),  # same sign
        _at("venus", ZodiacSign.ARIES),  # next sign: no aspect
        _at("moon", ZodiacSign.VIRGO),  # opposition, stays all day
        _at("mercury", ZodiacSign.TAURUS),  # sextile at the start, leaves the sign
        _at("sun", ZodiacSign.SCORPIO),  # never read
    ]
    end = [*start[:5], _at("mercury", ZodiacSign.GEMINI), start[6]]
    assert sky_contacts("pisces", start, end) == (
        "moon:tense",
        "mars:conj",
        "jupiter:coop",
        "saturn:tense",
    )


def test_the_moon_counts_only_on_days_it_keeps_its_sign() -> None:
    moving = sky_contacts(
        "pisces", [_at("moon", ZodiacSign.VIRGO)], [_at("moon", ZodiacSign.LIBRA)]
    )
    assert moving == ()
    with pytest.raises(ValueError):
        sky_contacts("unknown", [], [])


def _plan(contacts: tuple[str, ...] | None) -> ReadingPlan:
    result = _date_only_snapshot(GUEST, OWNER_A).result
    return ReadingPlanner().plan(
        result,
        purpose=ReadingPurpose.DAILY_NOTE,
        editorial_seed=START.isoformat(),
        daily_variety=DailyVariety(
            key_version=VARIETY_KEY_VERSION,
            catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
            seed="0" * 32,
            day_index=day_index(START),
            topic_history=(),
            sky_contacts=contacts,
        ),
    )


def test_a_sky_contact_adds_its_pair_rule_and_a_pending_one_adds_nothing() -> None:
    base = {situation.issue_key for situation in eligible_daily_situations(_plan(None))}
    # Saturn square the Sun: the existing Sun-Saturn rule (approved sentence).
    with_saturn = eligible_daily_situations(_plan(("saturn:tense",)))
    added = [situation for situation in with_saturn if situation.rule_key.startswith("sky-")]
    assert [situation.issue_key for situation in added] == ["comparison-loop"]
    assert {situation.issue_key for situation in with_saturn} == base | {"comparison-loop"}
    # Mars square the Sun has only a registry rule, still pending: nothing is added.
    pending = eligible_daily_situations(_plan(("mars:tense",)))
    assert {situation.issue_key for situation in pending} == base
    # The situation rests on the Sun factor alone: no Moon, angle or house (AC08).
    assert all(len(situation.factor_refs) == 1 for situation in added)


def test_a_card_from_a_sky_contact_passes_the_gates() -> None:
    plan = _plan(("saturn:tense",))
    sky = next(s for s in eligible_daily_situations(plan) if s.rule_key.startswith("sky-"))

    def pick(_: ReadingPlan, pool: list[SupportedSituation]) -> SupportedSituation:
        return sky

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(daily_psychology, "_pick", pick)
        card = DeterministicVietnameseRenderer().render(plan)
    assert card.semantic_blueprint is not None
    assert card.semantic_blueprint.mechanism_key == "psychology:comparison-loop"
    assert evaluate_candidate(plan, card).accepted


def test_plans_without_sky_keep_their_dump() -> None:
    variety = _plan(None).daily_variety
    assert variety is not None and "sky_contacts" not in variety.model_dump(mode="json")


def _service(repository: MemoryReadingRepository, sky: bool) -> ReadingApplicationService:
    return ReadingApplicationService(
        repository,
        NatalChartEngine(),
        daily_variety_key=KEY,
        daily_variety_from=START,
        daily_topic_schedule_from=START,
        daily_date_only_sky_from=START if sky else None,
    )


async def test_the_setting_is_off_by_default_and_needs_a_certain_sign() -> None:
    snapshot = _date_only_snapshot(GUEST, OWNER_A)
    off_repository = MemoryReadingRepository()
    off = await _open(_service(off_repository, sky=False), snapshot, START)
    plan = _stored_plan(off_repository, off.active.revision_id)
    assert plan.daily_variety is not None and plan.daily_variety.sky_contacts is None

    on_repository = MemoryReadingRepository()
    on = await _open(_service(on_repository, sky=True), snapshot, START)
    plan = _stored_plan(on_repository, on.active.revision_id)
    assert plan.daily_variety is not None and plan.daily_variety.sky_contacts is not None

    cusp = DateOnlySunResult(
        status="ambiguous",
        sign=None,
        candidates=(ZodiacSign.PISCES, ZodiacSign.ARIES),
        provenance=snapshot.result.provenance,
    )
    service = _service(MemoryReadingRepository(), sky=True)
    assert service._sky_contacts(cusp, START) is None


async def test_recomputed_history_is_what_a_sky_date_only_reader_was_served() -> None:
    snapshot = _date_only_snapshot(GUEST, OWNER_A)
    repository = MemoryReadingRepository()
    service = _service(repository, sky=True)
    served: dict[date, str] = {}
    headlines: dict[date, str] = {}
    sizes: list[int] = []
    for offset in range(20):
        day = START + timedelta(days=offset)
        projection = await _open(service, snapshot, day)
        candidate: Any = _served(repository, projection)
        served[day] = candidate.semantic_blueprint.mechanism_key.removeprefix("psychology:")
        headlines[day] = candidate.hook
        plan = _stored_plan(repository, projection.active.revision_id)
        assert plan.daily_variety is not None and plan.daily_variety.sky_contacts is not None
        sizes.append(len(plan.daily_variety.sky_contacts))
        assert served[day] == await service._computed_daily_issue(
            OWNER_A,
            snapshot.result,
            day,
            None,
            topic_history=plan.daily_variety.topic_history,
        )
    assert max(sizes) >= 1  # the sky is read on these days
    days = [served[START + timedelta(days=n)] for n in range(20)]
    assert all(a != b for a, b in pairwise(days))
    # A topic that returns brings a different headline than last time (per-appearance order).
    last_headline: dict[str, str] = {}
    for offset in range(20):
        day = START + timedelta(days=offset)
        headline = headlines[day]
        if served[day] in last_headline:
            assert headline != last_headline[served[day]], (day, served[day])
        last_headline[served[day]] = headline


def test_the_snapshot_keeps_only_the_sign() -> None:
    # Nothing in the date-only result names the birth date; the sky path never needs it.
    result = _date_only_snapshot(GUEST, OWNER_A).result
    assert "birth_date" not in DateOnlySunResult.model_fields
    assert isinstance(result, DateOnlySunResult) and result.sign is ZodiacSign.PISCES
