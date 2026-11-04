"""Daily v2 C2c: the passes of one slow transit form one episode.

Every chart here is synthetic: a made-up birth instant and coordinate, with one natal point then
moved to a longitude derived from the bundled Swiss Ephemeris (a station of Saturn or Mars after
2026-11-02), so the retrograde geometry is known. No real person's chart or birth data is used.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise

import pytest

from app.domains.astro.aspects import calculate_aspects
from app.domains.astro.engine import NatalChartEngine, sign_for_longitude
from app.domains.astro.models import BodyName, ChartInput, NatalChart, TimePrecision
from app.domains.daily.house_confidence import Birthplace, ChartAngle
from app.domains.daily.sky_selection import (
    DAILY_TIMEZONE,
    EXACT_ORB,
    MAX_SPEED_DEG_PER_DAY,
    SPEED_MARGIN,
    DayContact,
    PassKind,
    daily_house_frame,
    natal_domains,
    scan_day,
    select_daily_sky,
)
from app.domains.daily.transit_episodes import (
    MIN_STATION_GAP_DAYS,
    REVERSE_ARC_DEG,
    REVERSE_ARC_MARGIN_DEG,
    TRANSIT_EPISODE_VERSION,
    PassMotion,
    TransitEpisode,
    episode_stride,
    trend_episode,
)

START = date(2026, 11, 2)
SATURN_MARS = "saturn:conjunction:mars"
SYNTHETIC_BIRTHS = (
    (datetime(1984, 2, 11, 5, 40, tzinfo=UTC), 15.9, 108.3),
    (datetime(1993, 8, 23, 17, 15, tzinfo=UTC), 21.0, 105.8),
)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


@pytest.fixture(scope="module")
def charts(engine: NatalChartEngine) -> tuple[NatalChart, ...]:
    return tuple(
        engine.calculate_chart(ChartInput(utc_datetime=born, latitude=lat, longitude=lon))
        for born, lat, lon in SYNTHETIC_BIRTHS
    )


@pytest.fixture(scope="module")
def saturn(engine: NatalChartEngine) -> dict[str, tuple[date, float]]:
    """Saturn's retrograde station of mid-2026, direct station after START, and the next one."""

    found = _stations(engine, BodyName.SATURN, START - timedelta(days=200), 3)
    names = ("retrograde_2026", "direct", "retrograde_2027")
    assert [turns_direct for _, _, turns_direct in found] == [False, True, False]
    return {name: (day, longitude) for name, (day, longitude, _) in zip(names, found, strict=True)}


def _noon(day: date) -> datetime:
    return datetime.combine(day, time(12), tzinfo=DAILY_TIMEZONE)


def _wrap(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def _stations(
    engine: NatalChartEngine, body: BodyName, after: date, count: int
) -> list[tuple[date, float, bool]]:
    """``(local date, longitude, turns direct)`` of the next stations, from daily noon samples."""

    found: list[tuple[date, float, bool]] = []
    day = after
    speed = engine.transiting_position(body, _noon(day)).longitude_speed
    while len(found) < count:
        day += timedelta(days=1)
        position = engine.transiting_position(body, _noon(day))
        if (position.longitude_speed > 0) != (speed > 0):
            found.append((day, position.longitude, position.longitude_speed > 0))
        speed = position.longitude_speed
    return found


def _move_natal(chart: NatalChart, body: BodyName, longitude: float) -> NatalChart:
    moved = tuple(
        item.model_copy(
            update={
                "longitude": longitude % 360,
                "sign": sign_for_longitude(longitude),
                "degree_in_sign": (longitude % 360) % 30,
            }
        )
        if item.body is body
        else item
        for item in chart.bodies
    )
    return chart.model_copy(update={"bodies": moved, "aspects": calculate_aspects(moved)})


def _contact(engine: NatalChartEngine, chart: NatalChart, key: str, day: date) -> DayContact | None:
    return {item.id: item for item in scan_day(engine, chart, day)}.get(key)


def _first_in_orb(
    engine: NatalChartEngine, chart: NatalChart, key: str, after: date
) -> tuple[date, DayContact]:
    day = after
    for _ in range(800):
        contact = _contact(engine, chart, key, day)
        if contact is not None:
            return day, contact
        day += timedelta(days=1)
    raise AssertionError(f"{key} never in orb after {after}")


def _episode(engine: NatalChartEngine, chart: NatalChart, key: str, day: date) -> TransitEpisode:
    contact = _contact(engine, chart, key, day)
    assert contact is not None, (key, day)
    return trend_episode(engine, chart, contact, day)


def _hourly(
    engine: NatalChartEngine, body: BodyName, point: float, first: date, last: date
) -> list[tuple[datetime, float]]:
    """Signed separation from ``point`` every hour of the local days ``first..last``."""

    origin = datetime.combine(first, time(), tzinfo=DAILY_TIMEZONE)
    instants = [
        origin + timedelta(hours=hour) for hour in range(((last - first).days + 1) * 24 + 1)
    ]
    return [(at, _wrap(engine.transiting_position(body, at).longitude - point)) for at in instants]


def _brute_force(
    engine: NatalChartEngine, body: BodyName, point: float, reach: float, first: date, last: date
) -> tuple[set[date], list[datetime]]:
    """In-orb local days (at some hour of 00:00..24:00) and exact crossings, hourly."""

    samples = _hourly(engine, body, point, first, last)
    days: set[date] = set()
    for offset in range((last - first).days + 1):
        day = [value for _, value in samples[offset * 24 : offset * 24 + 25]]
        if any(abs(value) <= reach for value in day) or any(
            (left >= 0) != (right >= 0) for left, right in pairwise(day)
        ):
            days.add(first + timedelta(days=offset))
    crossings = [
        left_at for (left_at, left), (_, right) in pairwise(samples) if (left >= 0) != (right >= 0)
    ]
    return days, crossings


def _assert_matches_brute_force(
    engine: NatalChartEngine, episode: TransitEpisode, point: float, reach: float
) -> None:
    first = episode.start_date - timedelta(days=3)
    last = episode.end_date + timedelta(days=3)
    days, crossings = _brute_force(engine, episode.transit_body, point, reach, first, last)
    for offset in range((last - first).days + 1):
        day = first + timedelta(days=offset)
        assert episode.in_orb_on(day) is (day in days), day
    # Edges are exact to the day: in orb on the first/last day, out of orb just outside.
    assert episode.start_date in days and episode.end_date in days
    assert episode.start_date - timedelta(days=1) not in days
    assert episode.end_date + timedelta(days=1) not in days
    exact = [item.at for item in episode.passes if item.motion is not PassMotion.STATIONARY]
    assert len(exact) == len(crossings)
    for found, expected in zip(exact, crossings, strict=True):
        assert expected - timedelta(minutes=1) <= found <= expected + timedelta(hours=1)


def _saturn_chart(charts: tuple[NatalChart, ...], natal_longitude: float) -> NatalChart:
    return _move_natal(charts[0], BodyName.MARS, natal_longitude)


def test_retrograde_triple_pass_is_one_episode(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    saturn: dict[str, tuple[date, float]],
) -> None:
    """Saturn crosses a point inside its loop direct, retrograde, then direct again (AS-2)."""

    station_day, station_longitude = saturn["direct"]
    turn_day, _ = saturn["retrograde_2026"]
    point = station_longitude + 0.8
    chart = _saturn_chart(charts, point)
    first_day, contact = _first_in_orb(engine, chart, SATURN_MARS, START - timedelta(days=330))
    episode = trend_episode(engine, chart, contact, first_day)

    assert episode.version == TRANSIT_EPISODE_VERSION
    assert episode.contact_id == SATURN_MARS
    assert not episode.start_open and not episode.end_open
    assert episode.start_date == first_day
    assert episode.pass_count == 3
    assert [item.motion for item in episode.passes] == [
        PassMotion.DIRECT,
        PassMotion.RETROGRADE,
        PassMotion.DIRECT,
    ]
    assert all(item.kind is PassKind.EXACT and item.orb == 0.0 for item in episode.passes)
    first, second, third = (item.date for item in episode.passes)
    assert first < turn_day < second < station_day < third
    # Out of orb around the retrograde station: two segments, still one episode.
    assert len(episode.segments) == 2
    assert not episode.in_orb_on(turn_day)
    assert episode.peak is episode.passes[0]
    assert episode.key == f"{SATURN_MARS}@{first_day.isoformat()}"
    _assert_matches_brute_force(engine, episode, point, contact.orb_limit)

    # Every day the contact is listed returns the same episode; between segments it is absent.
    checked = 0
    span = (episode.end_date - episode.start_date).days
    for offset in sorted({*range(0, span + 1, 9), span}):
        day = episode.start_date + timedelta(days=offset)
        listed = _contact(engine, chart, SATURN_MARS, day)
        assert (listed is not None) is episode.in_orb_on(day), day
        if listed is not None:
            assert trend_episode(engine, chart, listed, day) == episode
            checked += 1
    assert checked >= 15


def test_station_on_the_point_keeps_every_crossing(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    saturn: dict[str, tuple[date, float]],
) -> None:
    """A station 0.1° past the point: the retrograde and direct crossings are weeks apart."""

    station_day, station_longitude = saturn["direct"]
    point = station_longitude + 0.1
    chart = _saturn_chart(charts, point)
    episode = _episode(engine, chart, SATURN_MARS, station_day)
    assert episode.pass_count == 3
    assert [item.motion for item in episode.passes] == [
        PassMotion.DIRECT,
        PassMotion.RETROGRADE,
        PassMotion.DIRECT,
    ]
    _, second, third = episode.passes
    assert second.date < station_day < third.date
    assert (third.date - second.date).days < 120
    _assert_matches_brute_force(engine, episode, point, 2.0)


@pytest.mark.parametrize(
    ("station", "offset", "motions"),
    [
        # The point lies before the direct station: crossed once, then a near miss at the turn.
        ("direct", -0.8, [PassMotion.DIRECT, PassMotion.STATIONARY]),
        # The point lies past the retrograde station: a near miss first, then one crossing.
        ("retrograde_2027", 0.8, [PassMotion.STATIONARY, PassMotion.DIRECT]),
    ],
)
def test_only_two_passes_when_the_station_turns_back_inside_the_orb(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    saturn: dict[str, tuple[date, float]],
    station: str,
    offset: float,
    motions: list[PassMotion],
) -> None:
    station_day, station_longitude = saturn[station]
    point = station_longitude + offset
    chart = _saturn_chart(charts, point)
    episode = _episode(engine, chart, SATURN_MARS, station_day)
    assert not episode.start_open and not episode.end_open
    assert episode.pass_count == 2
    assert [item.motion for item in episode.passes] == motions
    near_miss = next(item for item in episode.passes if item.motion is PassMotion.STATIONARY)
    assert abs((near_miss.date - station_day).days) <= 1
    assert near_miss.kind is PassKind.CLOSEST
    assert near_miss.orb == pytest.approx(abs(offset), abs=0.01)
    crossing = next(item for item in episode.passes if item.motion is PassMotion.DIRECT)
    assert crossing.kind is PassKind.EXACT
    assert episode.peak is crossing
    assert len(episode.segments) == 2  # the far station of the loop is out of orb
    _assert_matches_brute_force(engine, episode, point, 2.0)


@pytest.mark.parametrize(("margin", "segments"), [(-0.05, 2), (0.05, 3)])
def test_station_at_the_orb_boundary_splits_segments_not_the_episode(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    saturn: dict[str, tuple[date, float]],
    margin: float,
    segments: int,
) -> None:
    """The far station sits 0.05° inside or outside the 2° orb: same episode and passes."""

    turn_day, turn_longitude = saturn["retrograde_2026"]
    point = turn_longitude - (2.0 + margin)
    chart = _saturn_chart(charts, point)
    day, contact = _first_in_orb(engine, chart, SATURN_MARS, turn_day - timedelta(days=200))
    episode = trend_episode(engine, chart, contact, day)
    assert not episode.start_open and not episode.end_open
    assert episode.pass_count == 3
    assert [item.motion for item in episode.passes] == [
        PassMotion.DIRECT,
        PassMotion.RETROGRADE,
        PassMotion.DIRECT,
    ]
    assert len(episode.segments) == segments
    assert episode.in_orb_on(turn_day) is (margin < 0)
    _assert_matches_brute_force(engine, episode, point, contact.orb_limit)


def test_pass_on_the_scan_edge_is_kept_and_nothing_is_claimed_past_it(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    saturn: dict[str, tuple[date, float]],
) -> None:
    _, station_longitude = saturn["direct"]
    chart = _saturn_chart(charts, station_longitude + 0.8)
    day, contact = _first_in_orb(engine, chart, SATURN_MARS, START - timedelta(days=330))
    full = trend_episode(engine, chart, contact, day)
    last_pass = full.passes[-1].date
    bound = (last_pass - day).days

    on_edge = trend_episode(engine, chart, contact, day, max_scan_days=bound)
    assert on_edge.end_open and not on_edge.start_open
    assert on_edge.end_date == last_pass
    assert on_edge.passes == full.passes
    assert on_edge.key == full.key  # the start is known, so the key is too

    before_edge = trend_episode(engine, chart, contact, day, max_scan_days=bound - 1)
    assert before_edge.end_open
    assert before_edge.end_date == last_pass - timedelta(days=1)
    assert before_edge.passes == full.passes[:2]

    # A few days around a day between passes: both edges open, no pass invented at an edge.
    middle = full.passes[1].date + timedelta(days=20)
    listed = _contact(engine, chart, SATURN_MARS, middle)
    assert listed is not None
    short = trend_episode(engine, chart, listed, middle, max_scan_days=3)
    assert short.start_open and short.end_open
    assert (short.start_date, short.end_date) == (
        middle - timedelta(days=3),
        middle + timedelta(days=3),
    )
    assert short.passes == () and short.peak is None and short.key is None


def test_the_same_aspect_from_the_other_side_is_another_episode(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    """Mars trines the point near its station; months later it trines it from the other side."""

    station_day, station_longitude, _ = _stations(engine, BodyName.MARS, START, 1)[0]
    point = station_longitude - 121.0  # Mars stations 1° inside the trine
    chart = _move_natal(charts[1], BodyName.SATURN, point)
    key = "mars:trine:saturn"
    episode = _episode(engine, chart, key, station_day)
    assert not episode.start_open and not episode.end_open
    assert episode.pass_count == 3
    for item in episode.passes:
        longitude = engine.transiting_position(BodyName.MARS, item.at).longitude
        assert abs(_wrap(longitude - (point + 120.0))) < 0.05

    later_day, _ = _first_in_orb(engine, chart, key, episode.end_date + timedelta(days=1))
    later = _episode(engine, chart, key, later_day)
    assert later.start_date > episode.end_date
    assert later.key != episode.key
    longitude = engine.transiting_position(BodyName.MARS, _noon(later_day)).longitude
    assert abs(_wrap(longitude - (point - 120.0))) <= 2.5


def test_selection_attaches_one_episode_per_trend_contact(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    seen = 0
    for chart in charts:
        selection = select_daily_sky(engine, chart, START)
        assert selection == select_daily_sky(engine, chart, START)
        for item in selection.trend:
            episode = item.episode
            assert episode is not None
            assert episode.contact_id == item.contact.id
            assert episode.start_date <= START <= episode.end_date
            assert episode.in_orb_on(START)
            assert [entry.at for entry in episode.passes] == sorted(
                entry.at for entry in episode.passes
            )
            assert all(
                (entry.kind is PassKind.EXACT) is (entry.orb <= EXACT_ORB)
                for entry in episode.passes
            )
            assert (episode.key is None) is episode.start_open
            seen += 1
        bare = select_daily_sky(engine, chart, START, include_trend_windows=False)
        assert all(item.episode is None for item in bare.trend)
    assert seen >= 4


def test_non_exact_birth_time_reports_worst_case_pass_orbs(engine: NatalChartEngine) -> None:
    born = datetime.combine(date(1990, 3, 14), time(12), tzinfo=DAILY_TIMEZONE)
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=born.astimezone(UTC), latitude=16.0, longitude=108.0)
    ).model_copy(update={"time_precision": TimePrecision.UNKNOWN})
    domains = natal_domains(engine, chart)
    seen = 0
    for day in (START, START + timedelta(days=120)):
        for item in select_daily_sky(engine, chart, day).trend:
            assert item.episode is not None
            low, high = domains[item.contact.natal_body]
            half_width = (high - low) / 2
            for entry in item.episode.passes:
                assert entry.orb >= round(half_width, 4) - 1e-4
                if entry.motion is not PassMotion.STATIONARY:
                    assert entry.orb == pytest.approx(half_width, abs=1e-4)
                assert (entry.kind is PassKind.EXACT) is (entry.orb <= EXACT_ORB)
                seen += 1
    assert seen >= 1


def test_strides_and_jumps_never_skip_a_station(engine: NatalChartEngine) -> None:
    """The measured constants hold over 2026-2031, and the scan steps stay below them."""

    for body, arc in REVERSE_ARC_DEG.items():
        if body is BodyName.TRUE_NODE:
            assert episode_stride(body) == 1
            continue
        speed = MAX_SPEED_DEG_PER_DAY[body] * SPEED_MARGIN
        longest_jump = math.ceil((arc + REVERSE_ARC_MARGIN_DEG) / speed)
        assert max(episode_stride(body), longest_jump) < MIN_STATION_GAP_DAYS[body], body
        stations = _stations(engine, body, date(2026, 1, 1), 8)
        for (left_day, left, left_direct), (right_day, right, _) in pairwise(stations):
            assert (right_day - left_day).days >= MIN_STATION_GAP_DAYS[body] - 1, body
            if not left_direct:  # a retrograde arc runs from this station to the next
                assert abs(_wrap(right - left)) <= arc, body


def test_a_contact_to_a_chart_angle_keeps_the_angle_as_its_natal_point(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    """Slow transits to the Ascendant or Midheaven are episodes too (regression, PR #216)."""

    for chart, (_, latitude, longitude) in zip(charts, SYNTHETIC_BIRTHS, strict=True):
        # A reliable time keeps the angle domains narrower than the orb (see test_house_confidence).
        frame = daily_house_frame(
            engine,
            chart,
            Birthplace(latitude=latitude, longitude=longitude),
            exact_time_error_minutes=0.0,
        )
        assert frame is not None
        domains = natal_domains(engine, chart, houses=frame)
        day = START
        for _ in range(400):
            angle_contacts = [
                item
                for listed in scan_day(engine, chart, day, domains=domains, houses=frame)
                for item in (listed, *listed.merged)
                if isinstance(item.natal_body, ChartAngle) and episode_stride(item.transit_body) > 1
            ]
            if angle_contacts:
                contact = angle_contacts[0]
                episode = trend_episode(engine, chart, contact, day, domains=domains)
                assert episode.natal_body is contact.natal_body
                assert isinstance(episode.natal_body, ChartAngle)
                assert episode.contact_id == contact.id
                assert episode.in_orb_on(day)
                return
            day += timedelta(days=7)
    raise AssertionError("no slow contact to a chart angle in the synthetic charts")


def test_invalid_scan_bound_and_domain_wider_than_the_orb(engine: NatalChartEngine) -> None:
    born = datetime.combine(date(1990, 3, 14), time(12), tzinfo=DAILY_TIMEZONE)
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=born.astimezone(UTC), latitude=16.0, longitude=108.0)
    ).model_copy(update={"time_precision": TimePrecision.UNKNOWN})
    selection = select_daily_sky(engine, chart, START, include_trend_windows=False)
    contact = selection.trend[0].contact
    with pytest.raises(ValueError, match="max_scan_days"):
        trend_episode(engine, chart, contact, START, max_scan_days=0)
    low, high = natal_domains(engine, chart)[contact.natal_body]
    narrow = replace(contact, orb_limit=(high - low) / 4)
    with pytest.raises(ValueError, match="wider than the orb"):
        trend_episode(engine, chart, narrow, START)
