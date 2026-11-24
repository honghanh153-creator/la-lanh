"""Which real transit carries a topic this month, and when it is a little easier (AK2, 20.11.2026).

Everything here is geometry: no copy, no randomness, no clock. The same chart, topic and month give
the same fact; the same chart, topic and start day give the same window.

- **Houses.** A chart with an exact birth time uses its own house cusps. Any other chart uses
  whole-sign houses counted from the Sun's sign (the "solar chart"), because a house from an
  approximate or unknown time is a guess. A date-only profile whose Sun sits on a sign change has
  no Sun sign, so it has no houses at all: its fact is the topic's planet in its sky sign.
- **Month fact.** The six planets that move enough in a month (Sun, Mercury, Venus, Mars, Jupiter,
  Saturn) are sampled at noon in Vietnam on every day of the month. The planet that spends the most
  weighted days in the topic's houses carries the topic. Slow planets weigh less, so the answer
  follows what changes this month rather than what stays for two years. When no planet visits the
  topic's houses for at least ``MIN_DAYS`` days, the ruler of the topic's first house carries it.
- **Window.** The run of days, from the start day on, when the Moon is in the topic's houses
  (for a profile without houses: in a sign of the same element as the month planet). Only easier
  days exist here; there is no "bad day" concept to compute.
"""

from __future__ import annotations

from calendar import monthrange
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine, house_for_longitude, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    CalculationConfig,
    DateOnlySunResult,
    NatalChart,
    TimePrecision,
    ZodiacSign,
)

PRODUCT_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
FACTS_VERSION = "month-facts-v1"
MIN_DAYS = 5
WINDOW_SEARCH_DAYS = 35
WINDOW_MAX_DAYS = 3


class Topic(StrEnum):
    WORK = "work"
    MONEY = "money"
    LOVE = "love"
    FAMILY = "family"
    STUDY = "study"
    MIND = "mind"


class HouseBasis(StrEnum):
    NATAL = "natal"  # cusps from an exact birth time
    SOLAR = "solar"  # whole-sign houses from the Sun's sign
    NONE = "none"  # no Sun sign: sky sign only


class FactKind(StrEnum):
    IN_HOUSE = "in_house"
    RULER = "ruler"
    SKY = "sky"


# Topic houses, first one is the topic's own house (its ruler is the fallback).
TOPIC_HOUSES: dict[Topic, tuple[int, ...]] = {
    Topic.WORK: (10, 6),
    Topic.MONEY: (2, 8),
    Topic.LOVE: (5, 7),
    Topic.FAMILY: (4,),
    Topic.STUDY: (3, 9),
    Topic.MIND: (12, 1),
}

# A planet for profiles without houses, chosen for the topic's usual meaning.
SKY_PLANET: dict[Topic, BodyName] = {
    Topic.WORK: BodyName.SATURN,
    Topic.MONEY: BodyName.JUPITER,
    Topic.LOVE: BodyName.VENUS,
    Topic.FAMILY: BodyName.SUN,
    Topic.STUDY: BodyName.MERCURY,
    Topic.MIND: BodyName.MARS,
}

MONTH_PLANETS: tuple[BodyName, ...] = (
    BodyName.MARS,
    BodyName.SUN,
    BodyName.MERCURY,
    BodyName.VENUS,
    BodyName.JUPITER,
    BodyName.SATURN,
)
# Fast planets weigh more: a month answer should follow what moves this month.
PLANET_WEIGHT: dict[BodyName, float] = {
    BodyName.MARS: 1.1,
    BodyName.SUN: 1.0,
    BodyName.MERCURY: 1.0,
    BodyName.VENUS: 1.0,
    BodyName.JUPITER: 0.8,
    BodyName.SATURN: 0.7,
}
# Answer copy exists for these planets (the month planets plus the Moon as a sign ruler).
ANSWER_PLANETS: tuple[BodyName, ...] = (*MONTH_PLANETS, BodyName.MOON)

SIGN_ORDER: tuple[ZodiacSign, ...] = tuple(ZodiacSign)
TRADITIONAL_RULER: dict[ZodiacSign, BodyName] = dict(
    zip(
        SIGN_ORDER,
        (
            BodyName.MARS,
            BodyName.VENUS,
            BodyName.MERCURY,
            BodyName.MOON,
            BodyName.SUN,
            BodyName.MERCURY,
            BodyName.VENUS,
            BodyName.MARS,
            BodyName.JUPITER,
            BodyName.SATURN,
            BodyName.SATURN,
            BodyName.JUPITER,
        ),
        strict=True,
    )
)


@dataclass(frozen=True, slots=True)
class MonthFact:
    """The one transit fact a month answer stands on."""

    topic: Topic
    month: str  # YYYY-MM
    kind: FactKind
    planet: BodyName
    house_basis: HouseBasis
    house: int | None  # where the planet spends most of the month (None without houses)
    sign: ZodiacSign  # the planet's sign on most days of the month
    days: int  # days of the month spent in ``house`` (or in ``sign`` without houses)
    ruled_house: int | None = None  # for RULER: the topic house it rules
    ruled_sign: ZodiacSign | None = None  # for RULER: the sign on that house
    solar_sign: ZodiacSign | None = None  # for SOLAR houses: the Sun sign they count from


@dataclass(frozen=True, slots=True)
class EasierWindow:
    start: date
    end: date
    house_basis: HouseBasis
    house: int | None
    sign: ZodiacSign | None  # the Moon's sign on the first day (sky profiles)


@dataclass(frozen=True, slots=True)
class _Frame:
    basis: HouseBasis
    config: CalculationConfig
    natal: NatalChart | None
    solar_sign: ZodiacSign | None

    def house_of(self, longitude: float) -> int | None:
        if self.basis is HouseBasis.NATAL and self.natal is not None and self.natal.houses:
            return house_for_longitude(longitude, self.natal.houses)
        if self.basis is HouseBasis.SOLAR and self.solar_sign is not None:
            offset = SIGN_ORDER.index(sign_for_longitude(longitude)) - SIGN_ORDER.index(
                self.solar_sign
            )
            return offset % 12 + 1
        return None

    def sign_on_house(self, house: int) -> ZodiacSign | None:
        if self.basis is HouseBasis.NATAL and self.natal is not None and self.natal.houses:
            cusp = next(item for item in self.natal.houses if item.number == house)
            return cusp.sign
        if self.basis is HouseBasis.SOLAR and self.solar_sign is not None:
            return SIGN_ORDER[(SIGN_ORDER.index(self.solar_sign) + house - 1) % 12]
        return None


def frame_for(result: NatalChart | DateOnlySunResult) -> _Frame:
    if isinstance(result, NatalChart):
        sun = next((body for body in result.bodies if body.body is BodyName.SUN), None)
        if (
            result.time_precision is TimePrecision.EXACT
            and result.houses is not None
            and len(result.houses) == 12
        ):
            return _Frame(HouseBasis.NATAL, result.config, result, sun.sign if sun else None)
        if sun is not None:
            return _Frame(HouseBasis.SOLAR, result.config, result, sun.sign)
        return _Frame(HouseBasis.NONE, result.config, result, None)
    config = CalculationConfig.western_recommended()
    if result.sign is not None:
        return _Frame(HouseBasis.SOLAR, config, None, result.sign)
    return _Frame(HouseBasis.NONE, config, None, None)


def local_noon(day: date) -> datetime:
    return datetime.combine(day, time(hour=12), tzinfo=PRODUCT_TIMEZONE).astimezone(UTC)


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def month_days(month: str) -> tuple[date, ...]:
    year, number = (int(part) for part in month.split("-"))
    return tuple(date(year, number, day) for day in range(1, monthrange(year, number)[1] + 1))


def _positions(
    engine: NatalChartEngine, day: date, config: CalculationConfig
) -> dict[BodyName, BodyPosition]:
    return {body.body: body for body in engine.transiting_positions(local_noon(day), config)}


def month_fact(
    engine: NatalChartEngine,
    result: NatalChart | DateOnlySunResult,
    topic: Topic,
    month: str,
) -> MonthFact:
    frame = frame_for(result)
    days = month_days(month)
    skies = [_positions(engine, day, frame.config) for day in days]

    if frame.basis is HouseBasis.NONE:
        planet = SKY_PLANET[topic]
        sky_signs: Counter[ZodiacSign] = Counter(sky[planet].sign for sky in skies)
        sign, count = _most_common(sky_signs, SIGN_ORDER)
        return MonthFact(topic, month, FactKind.SKY, planet, frame.basis, None, sign, count)

    wanted = TOPIC_HOUSES[topic]
    best: tuple[float, int] | None = None
    best_fact: MonthFact | None = None
    for rank, planet in enumerate(MONTH_PLANETS):
        houses: Counter[int | None] = Counter()
        signs: Counter[ZodiacSign] = Counter()
        for sky in skies:
            place = frame.house_of(sky[planet].longitude)
            if place in wanted:
                houses[place] += 1
                signs[sky[planet].sign] += 1
        inside = sum(houses.values())
        if inside < MIN_DAYS:
            continue
        score = (inside * PLANET_WEIGHT[planet], -rank)
        if best is None or score > best:
            top_house, _ = _most_common(houses, wanted)
            sign, _ = _most_common(signs, SIGN_ORDER)
            best = score
            best_fact = MonthFact(
                topic,
                month,
                FactKind.IN_HOUSE,
                planet,
                frame.basis,
                top_house,
                sign,
                inside,
                solar_sign=frame.solar_sign if frame.basis is HouseBasis.SOLAR else None,
            )
    if best_fact is not None:
        return best_fact

    ruled_house = wanted[0]
    ruled_sign = frame.sign_on_house(ruled_house)
    if ruled_sign is None:  # a frame with houses always has a sign on each house
        raise ValueError("house frame without a sign on its first topic house")
    ruler = TRADITIONAL_RULER[ruled_sign]
    ruler_houses: Counter[int | None] = Counter(
        frame.house_of(sky[ruler].longitude) for sky in skies
    )
    ruler_signs: Counter[ZodiacSign] = Counter(sky[ruler].sign for sky in skies)
    ruler_house, count = _most_common(ruler_houses, tuple(range(1, 13)))
    sign, _ = _most_common(ruler_signs, SIGN_ORDER)
    house: int | None = ruler_house
    if ruler is BodyName.MOON:
        # The Moon crosses every house in a month: name no single house for it.
        house, count = None, len(days)
    return MonthFact(
        topic,
        month,
        FactKind.RULER,
        ruler,
        frame.basis,
        house,
        sign,
        count,
        ruled_house=ruled_house,
        ruled_sign=ruled_sign,
        solar_sign=frame.solar_sign if frame.basis is HouseBasis.SOLAR else None,
    )


def easier_window(
    engine: NatalChartEngine,
    result: NatalChart | DateOnlySunResult,
    topic: Topic,
    start: date,
) -> EasierWindow | None:
    """The first run of easier days from ``start`` on (at most ``WINDOW_MAX_DAYS`` long)."""

    frame = frame_for(result)
    wanted = TOPIC_HOUSES[topic]
    element_signs: frozenset[ZodiacSign] = frozenset()
    if frame.basis is HouseBasis.NONE:
        planet = SKY_PLANET[topic]
        planet_sign = _positions(engine, start, frame.config)[planet].sign
        index = SIGN_ORDER.index(planet_sign)
        element_signs = frozenset(SIGN_ORDER[(index + step) % 12] for step in (0, 4, 8))

    run: list[tuple[date, int | None, ZodiacSign]] = []
    for offset in range(WINDOW_SEARCH_DAYS):
        day = start + timedelta(days=offset)
        moon = engine.transiting_position(BodyName.MOON, local_noon(day), frame.config)
        house = frame.house_of(moon.longitude)
        easy = moon.sign in element_signs if frame.basis is HouseBasis.NONE else house in wanted
        if easy:
            run.append((day, house, moon.sign))
            if len(run) == WINDOW_MAX_DAYS:
                break
        elif run:
            break
    if not run:
        return None
    first_day, first_house, first_sign = run[0]
    return EasierWindow(
        start=first_day,
        end=run[-1][0],
        house_basis=frame.basis,
        house=first_house,
        sign=first_sign if frame.basis is HouseBasis.NONE else None,
    )


def _most_common[T](counter: Counter[T], order: tuple[T, ...]) -> tuple[T, int]:
    """Highest count; ties go to the earliest item in ``order`` (never to dict order)."""

    top = max(counter.values())
    for item in order:
        if counter.get(item, 0) == top:
            return item, top
    raise ValueError("empty counter")
