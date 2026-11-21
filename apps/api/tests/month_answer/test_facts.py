"""The month fact and the easier window come from real transits and are deterministic."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime

import pytest

from app.domains.astro.engine import NatalChartEngine, house_for_longitude
from app.domains.astro.models import (
    BodyName,
    ChartInput,
    DateOnlySunResult,
    NatalChart,
    TimePrecision,
)
from app.domains.month_answer.answer import compose
from app.domains.month_answer.facts import (
    TOPIC_HOUSES,
    FactKind,
    HouseBasis,
    Topic,
    easier_window,
    frame_for,
    local_noon,
    month_fact,
)
from app.domains.month_answer.presets import PresetId, presets_for

DATE_LIKE = re.compile(r"\b\d{1,2}\s*[./-]\s*\d{1,2}\b|\bngày \d|\bmùng \d|\btháng \d|\d{4}-\d{2}")


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


def _chart(engine: NatalChartEngine, when: datetime, precision: TimePrecision) -> NatalChart:
    chart = engine.calculate_chart(ChartInput(utc_datetime=when, latitude=21.03, longitude=105.85))
    if precision is TimePrecision.EXACT:
        return chart
    return chart.model_copy(update={"time_precision": precision, "houses": None, "angles": None})


# Synthetic births, chosen only to spread the Sun and the Ascendant around the zodiac.
BIRTHS = (
    datetime(1993, 7, 21, 1, 30, tzinfo=UTC),
    datetime(1988, 2, 9, 14, 5, tzinfo=UTC),
    datetime(2001, 10, 30, 22, 45, tzinfo=UTC),
    datetime(1979, 5, 3, 8, 15, tzinfo=UTC),
)


def test_frame_follows_birth_time_precision(engine: NatalChartEngine) -> None:
    exact = _chart(engine, BIRTHS[0], TimePrecision.EXACT)
    approximate = _chart(engine, BIRTHS[0], TimePrecision.APPROXIMATE)
    assert frame_for(exact).basis is HouseBasis.NATAL
    assert frame_for(approximate).basis is HouseBasis.SOLAR
    certain = engine.calculate_date_only_sun(date(1993, 7, 21))
    assert frame_for(certain).basis is HouseBasis.SOLAR
    candidates = DateOnlySunResult(
        status="candidates", sign=None, candidates=certain.candidates, provenance=certain.provenance
    )
    assert frame_for(candidates).basis is HouseBasis.NONE


@pytest.mark.parametrize("birth", BIRTHS)
@pytest.mark.parametrize("topic", list(Topic))
def test_same_chart_topic_month_gives_the_same_fact(
    engine: NatalChartEngine, birth: datetime, topic: Topic
) -> None:
    chart = _chart(engine, birth, TimePrecision.EXACT)
    first = month_fact(engine, chart, topic, "2026-11")
    second = month_fact(NatalChartEngine(), chart, topic, "2026-11")
    assert first == second


@pytest.mark.parametrize("birth", BIRTHS)
def test_in_house_fact_is_true_on_the_days_it_counts(
    engine: NatalChartEngine, birth: datetime
) -> None:
    chart = _chart(engine, birth, TimePrecision.EXACT)
    assert chart.houses is not None
    for topic in Topic:
        fact = month_fact(engine, chart, topic, "2026-11")
        if fact.kind is not FactKind.IN_HOUSE:
            assert fact.kind is FactKind.RULER
            assert fact.ruled_house == TOPIC_HOUSES[topic][0]
            continue
        assert fact.house in TOPIC_HOUSES[topic]
        inside = 0
        for day in range(1, 31):
            sky = engine.transiting_position(fact.planet, local_noon(date(2026, 11, day)))
            if house_for_longitude(sky.longitude, chart.houses) in TOPIC_HOUSES[topic]:
                inside += 1
        assert inside == fact.days >= 5


def test_facts_change_with_the_month(engine: NatalChartEngine) -> None:
    chart = _chart(engine, BIRTHS[1], TimePrecision.EXACT)
    months = [f"2026-{number:02d}" for number in range(1, 13)]
    planets = {month_fact(engine, chart, Topic.WORK, month).planet for month in months}
    assert len(planets) >= 3  # the answer follows what moves, not one planet all year


def test_sky_fact_without_a_sun_sign(engine: NatalChartEngine) -> None:
    certain = engine.calculate_date_only_sun(date(1993, 7, 21))
    candidates = DateOnlySunResult(
        status="candidates", sign=None, candidates=certain.candidates, provenance=certain.provenance
    )
    fact = month_fact(engine, candidates, Topic.LOVE, "2026-11")
    assert fact.kind is FactKind.SKY and fact.house is None and fact.planet is BodyName.VENUS


@pytest.mark.parametrize("birth", BIRTHS)
@pytest.mark.parametrize("topic", list(Topic))
def test_window_is_real_short_and_starts_on_or_after_today(
    engine: NatalChartEngine, birth: datetime, topic: Topic
) -> None:
    chart = _chart(engine, birth, TimePrecision.EXACT)
    assert chart.houses is not None
    start = date(2026, 11, 20)
    window = easier_window(engine, chart, topic, start)
    assert window is not None
    assert start <= window.start <= window.end
    assert (window.end - window.start).days <= 2
    day = window.start
    while day <= window.end:
        moon = engine.transiting_position(BodyName.MOON, local_noon(day))
        assert house_for_longitude(moon.longitude, chart.houses) in TOPIC_HOUSES[topic]
        day = date.fromordinal(day.toordinal() + 1)
    assert window == easier_window(engine, chart, topic, start)


def test_answer_is_deterministic_and_holds_no_date(engine: NatalChartEngine, approve_month) -> None:  # type: ignore[no-untyped-def]
    approve_month()
    chart = _chart(engine, BIRTHS[2], TimePrecision.EXACT)
    for topic in Topic:
        fact = month_fact(engine, chart, topic, "2026-11")
        first = compose(fact)
        second = compose(month_fact(engine, chart, topic, "2026-11"))
        assert first is not None and first == second
        assert first.basis.line.startswith("Dựa vào: ")
        assert first.preset is None and first.question is None and first.tip is None
        text = " ".join((first.theme, first.act, first.say, first.basis.line, first.basis.detail))
        assert not DATE_LIKE.search(text)


def test_pending_copy_gives_no_answer(engine: NatalChartEngine) -> None:
    chart = _chart(engine, BIRTHS[0], TimePrecision.EXACT)
    fact = month_fact(engine, chart, Topic.WORK, "2026-11")
    assert compose(fact) is None


def test_preset_answer_keeps_the_chart_parts(engine: NatalChartEngine, approve_month) -> None:  # type: ignore[no-untyped-def]
    approve_month()
    chart = _chart(engine, BIRTHS[0], TimePrecision.EXACT)
    for topic in Topic:
        fact = month_fact(engine, chart, topic, "2026-11")
        plain = compose(fact)
        assert plain is not None
        keys = {plain.answer_key}
        for preset in presets_for(topic):
            answer = compose(fact, preset)
            assert answer is not None and answer.preset is preset
            assert answer.question and answer.question.endswith("?")
            assert answer.tip
            assert (answer.theme, answer.act, answer.say, answer.basis) == (
                plain.theme,
                plain.act,
                plain.say,
                plain.basis,
            )
            keys.add(answer.answer_key)
        assert len(keys) == 4  # each preset saves as its own answer


def test_preset_from_another_topic_is_refused(engine: NatalChartEngine, approve_month) -> None:  # type: ignore[no-untyped-def]
    approve_month()
    chart = _chart(engine, BIRTHS[0], TimePrecision.EXACT)
    fact = month_fact(engine, chart, Topic.WORK, "2026-11")
    with pytest.raises(ValueError):
        compose(fact, PresetId.MONEY_MONTH_END)


def test_window_ignores_the_clock_inside_a_day(engine: NatalChartEngine) -> None:
    chart = _chart(engine, BIRTHS[3], TimePrecision.EXACT)
    morning = easier_window(engine, chart, Topic.MONEY, date(2026, 11, 20))
    assert morning == easier_window(engine, chart, Topic.MONEY, date(2026, 11, 20))
    assert datetime(2026, 11, 20, 5, tzinfo=UTC) == local_noon(date(2026, 11, 20))
