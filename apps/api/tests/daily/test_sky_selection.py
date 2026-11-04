"""Daily v2 C2a: the day's sky factors in Vietnam time.

Every chart here is synthetic (made-up birth instants and coordinates), never a real person's.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domains.astro.aspects import (
    angular_distance,
    calculate_aspects,
    orb_bounds,
    transit_orb_limit,
)
from app.domains.astro.engine import NatalChartEngine, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    CalculationConfig,
    ChartInput,
    NatalChart,
    TimePrecision,
    TransitPhase,
)
from app.domains.daily.house_confidence import Birthplace, CuspSample, HouseFrame
from app.domains.daily.sky_selection import (
    DAILY_SELECTION_VERSION,
    DAILY_TIMEZONE,
    DAYS_TIER_MAX_DAYS,
    EXACT_ORB,
    INTERVAL_NATAL_BODIES,
    MAX_MOON_PICKS,
    NATAL_MOON_WINDOW_EXTRA_ORB,
    OUTER_BODIES,
    PEAK_ORB,
    WEEKS_TIER_MAX_DAYS,
    ContactEligibility,
    DayContact,
    DayTone,
    PassKind,
    SkyTier,
    TimeKind,
    contact_eligibility,
    day_bounds,
    day_tone,
    moon_context,
    natal_domains,
    pick_daily_factors,
    scan_day,
    score_contact,
    select_daily_sky,
    tier_for,
    trend_weight,
    trend_window,
    worst_orb,
)

SYNTHETIC_BIRTHS = (
    (datetime(1988, 6, 4, 3, 20, tzinfo=UTC), 16.05, 108.2),
    (datetime(1996, 11, 27, 14, 5, tzinfo=UTC), 10.8, 106.7),
    (datetime(2001, 2, 9, 22, 45, tzinfo=UTC), 20.86, 106.68),
    (datetime(1979, 9, 18, 8, 50, tzinfo=UTC), 12.25, 109.19),
)
START = date(2026, 11, 2)
FAST = {BodyName.MOON, BodyName.SUN, BodyName.MERCURY, BodyName.VENUS, BodyName.MARS}


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
def month(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> tuple[tuple[NatalChart, date, tuple[DayContact, ...]], ...]:
    """Thirty scanned days for every synthetic chart."""

    return tuple(
        (chart, START + timedelta(days=offset), scan_day(engine, chart, START + timedelta(offset)))
        for chart in charts
        for offset in range(30)
    )


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


def _find(contacts: tuple[DayContact, ...], key: str) -> DayContact:
    """A contact by id, also when it was merged into another factor."""

    for item in contacts:
        for candidate in (item, *item.merged):
            if candidate.id == key:
                return candidate
    raise KeyError(key)


def _local(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=DAILY_TIMEZONE)


def _contact(
    transit: BodyName,
    natal: BodyName,
    orb: float,
    *,
    exact_today: bool = False,
    kind: str = "trine",
    peak_hour: int | None = 12,
    phase: TransitPhase = TransitPhase.SEPARATING,
    stack: int = 0,
    triggers: tuple[str, ...] = (),
) -> DayContact:
    closest = _local(START, peak_hour) if peak_hour is not None else None
    contact = DayContact(
        id=f"{transit.value}:{kind}:{natal.value}",
        transit_body=transit,
        kind=kind,
        exact_angle={"trine": 120.0, "square": 90.0, "sextile": 60.0}.get(kind, 0.0),
        natal_body=natal,
        tier=tier_for(transit, exact_today=exact_today, span_days=5.0),
        min_orb=orb,
        orb_limit=2.5,
        closest_at=closest,
        phase=TransitPhase.EXACT if exact_today else phase,
        exact_today=exact_today,
        time_kind=TimeKind.PEAKS_TODAY if closest else TimeKind.IN_EFFECT_ALL_DAY,
        window_start=_local(START, 0),
        window_end=_local(START + timedelta(days=1), 0),
        stack=stack,
        triggers_trend=triggers,
    )
    return replace(contact, score=score_contact(contact))


@pytest.mark.parametrize(
    ("body", "exact_today", "span", "tier"),
    [
        (BodyName.MOON, False, None, SkyTier.TODAY),
        (BodyName.MOON, True, None, SkyTier.TODAY),
        (BodyName.SUN, True, 6.0, SkyTier.TODAY),
        (BodyName.MERCURY, False, 3.5, SkyTier.DAYS),
        (BodyName.VENUS, False, DAYS_TIER_MAX_DAYS, SkyTier.DAYS),
        (BodyName.MARS, False, 9.0, SkyTier.WEEKS),
        (BodyName.MARS, False, WEEKS_TIER_MAX_DAYS, SkyTier.WEEKS),
        (BodyName.MARS, False, None, SkyTier.TREND),
        (BodyName.MARS, True, None, SkyTier.TODAY),
        (BodyName.JUPITER, True, None, SkyTier.TREND),
        (BodyName.SATURN, False, None, SkyTier.TREND),
        (BodyName.PLUTO, False, None, SkyTier.TREND),
        (BodyName.CHIRON, False, None, SkyTier.TREND),
        (BodyName.TRUE_NODE, True, None, SkyTier.TREND),
        (BodyName.MEAN_NODE, False, None, SkyTier.TREND),
    ],
)
def test_tier_follows_planet_and_measured_length(
    body: BodyName, exact_today: bool, span: float | None, tier: SkyTier
) -> None:
    assert tier_for(body, exact_today=exact_today, span_days=span) is tier


def test_thirty_days_rotate_and_stay_diverse(
    month: tuple[tuple[NatalChart, date, tuple[DayContact, ...]], ...],
) -> None:
    repeats = comparisons = short_days = 0
    previous: dict[str, str] = {}
    for chart, _day, contacts in month:
        picks = pick_daily_factors(contacts)
        short_days += len(picks) < 3
        assert sum(item.transit_body is BodyName.MOON for item in picks) <= MAX_MOON_PICKS
        assert sum(item.transit_body not in FAST for item in picks) <= 1
        assert all(item.tier is not SkyTier.TREND or item.exact_today for item in picks)
        preferred = [item.preferred_natal for item in picks]
        assert preferred == sorted(preferred, reverse=True)  # thin points only fill the end
        key = chart.config_hash + str(chart.julian_day_ut)
        if key in previous:
            comparisons += 1
            repeats += picks[0].id == previous[key]
        previous[key] = picks[0].id
    assert short_days <= 2
    assert repeats / comparisons <= 0.10


def test_contact_timing_is_consistent_and_never_a_fake_sample_edge(
    month: tuple[tuple[NatalChart, date, tuple[DayContact, ...]], ...],
) -> None:
    kinds: set[TimeKind] = set()
    for _chart, day, contacts in month:
        start, end = (instant.astimezone(DAILY_TIMEZONE) for instant in day_bounds(day))
        for item in contacts:
            kinds.add(item.time_kind)
            assert start <= item.window_start <= item.window_end <= end
            assert (item.closest_at is not None) is (item.time_kind is TimeKind.PEAKS_TODAY)
            assert item.exact_today is (item.phase is TransitPhase.EXACT)
            assert item.exact_today is (item.closest_at is not None and item.min_orb <= EXACT_ORB)
            if item.closest_at is not None:
                assert start <= item.closest_at < end
                assert item.window_start <= item.closest_at <= item.window_end
                # A real interpolated peak, not the 00:00 / 23:30 sample edge.
                assert item.closest_at not in (start, end - timedelta(minutes=30))
            if item.peak_start is not None:
                assert item.peak_end is not None
                assert item.window_start <= item.peak_start <= item.peak_end <= item.window_end
                if item.closest_at is not None:
                    assert item.peak_start <= item.closest_at <= item.peak_end
            if item.time_kind is TimeKind.STARTS_TODAY:
                assert item.window_start > start and item.window_end == end
            if item.time_kind is TimeKind.ENDS_TODAY:
                assert item.window_start == start and item.window_end < end
            if item.time_kind in (TimeKind.IN_EFFECT_ALL_DAY, TimeKind.MULTI_DAY):
                assert (item.window_start, item.window_end) == (start, end)
                long_tier = item.tier in (SkyTier.WEEKS, SkyTier.TREND)
                assert (item.time_kind is TimeKind.MULTI_DAY) is long_tier
            if item.transit_body in FAST - {BodyName.MOON} and item.span_days is not None:
                assert item.tier is SkyTier.TODAY or (
                    (item.span_days <= DAYS_TIER_MAX_DAYS) is (item.tier is SkyTier.DAYS)
                )
    assert kinds == set(TimeKind)


def test_peak_window_uses_the_tight_orb(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    day = START + timedelta(days=3)
    exact_at = _local(day, 15)
    moon = engine.transiting_position(BodyName.MOON, exact_at, charts[0].config)
    chart = _move_natal(charts[0], BodyName.VENUS, moon.longitude)
    item = _find(scan_day(engine, chart, day), "moon:conjunction:venus")
    natal = chart.body(BodyName.VENUS).longitude
    assert item.peak_start is not None and item.peak_end is not None
    for edge in (item.peak_start, item.peak_end):
        longitude = engine.transiting_position(BodyName.MOON, edge, chart.config).longitude
        assert angular_distance(longitude, natal) == pytest.approx(PEAK_ORB, abs=0.02)
    # ~1° either side at ~13°/day: a few hours, well inside the 3° in-orb window.
    assert timedelta(hours=3) < item.peak_end - item.peak_start < timedelta(hours=5)
    assert item.window_end - item.window_start > item.peak_end - item.peak_start


def test_score_prefers_rare_applying_stacked_and_triggering_contacts() -> None:
    moon_exact = _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True)
    venus_exact = _contact(BodyName.VENUS, BodyName.SUN, 0.0, exact_today=True)
    assert venus_exact.score > moon_exact.score  # K-3: rarity beats the daily Moon
    applying = _contact(
        BodyName.SUN, BodyName.MARS, 1.5, peak_hour=None, phase=TransitPhase.APPROACHING
    )
    separating = _contact(BodyName.SUN, BodyName.MARS, 1.5, peak_hour=None)
    assert applying.score > separating.score  # AS-14
    stacked = _contact(BodyName.MOON, BodyName.VENUS, 0.0, exact_today=True, stack=2)
    alone = _contact(BodyName.MOON, BodyName.VENUS, 0.0, exact_today=True)
    assert stacked.score > alone.score  # AS-19
    trigger = _contact(
        BodyName.MOON, BodyName.MARS, 0.0, exact_today=True, triggers=("saturn:square:mars",)
    )
    plain = _contact(BodyName.MOON, BodyName.MARS, 0.0, exact_today=True)
    assert trigger.score > plain.score  # AS-3
    # Timing bonuses need a peak today: a background contact never outranks a Moon peak on a
    # personal point, so the top pick keeps rotating.
    background = _contact(
        BodyName.SUN, BodyName.SUN, 0.5, peak_hour=None, phase=TransitPhase.APPROACHING, stack=2
    )
    assert background.score < _contact(BodyName.MOON, BodyName.MERCURY, 0.0, exact_today=True).score
    asleep = _contact(BodyName.MOON, BodyName.VENUS, 0.0, exact_today=True, peak_hour=3)
    assert not asleep.waking and asleep.score < alone.score
    assert (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True, peak_hour=3).score
        > alone.score
    )


def test_phase_is_none_when_the_natal_domain_ends_disagree(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    # Spec §4: a synthetic natal Mercury domain [L-1°, L+1°] and the direct Moon at L at noon.
    day = START + timedelta(days=6)
    noon = _local(day, 12)
    config = charts[0].config
    moon = engine.transiting_position(BodyName.MOON, noon, config).longitude
    key = "moon:conjunction:mercury"
    domain = (moon - 1.0, moon + 1.0)
    wide = _find(scan_day(engine, charts[0], day, domains={BodyName.MERCURY: domain}), key)
    assert wide.closest_at is not None and abs(wide.closest_at - noon) <= timedelta(minutes=10)
    assert wide.min_orb == pytest.approx(1.0, abs=0.02)  # certainly in orb over the domain
    assert not wide.exact_today
    # Both ends are in orb at noon, one separating and one approaching, so no phase is stated.
    later = engine.transiting_position(BodyName.MOON, noon + timedelta(hours=1), config).longitude
    closing = []
    for natal in domain:
        assert angular_distance(moon, natal) <= wide.orb_limit
        closing.append(angular_distance(later, natal) < angular_distance(moon, natal))
    assert closing == [False, True]
    assert wide.phase is None
    # An uncertain phase earns no applying bonus.
    assert wide.score == score_contact(replace(wide, phase=TransitPhase.SEPARATING))
    assert wide.score < score_contact(replace(wide, phase=TransitPhase.APPROACHING))

    # A point domain keeps its certain phase.
    point = _find(scan_day(engine, charts[0], day, domains={BodyName.MERCURY: (moon, moon)}), key)
    assert point.phase is TransitPhase.EXACT
    # A domain the Moon only closes in on all day: both ends agree, so the phase is kept.
    end_moon = engine.transiting_position(
        BodyName.MOON, _local(day + timedelta(days=1), 0), config
    ).longitude
    ahead_domain = (end_moon + 1.0, end_moon + 1.5)
    ahead = _find(scan_day(engine, charts[0], day, domains={BodyName.MERCURY: ahead_domain}), key)
    assert ahead.closest_at is None and ahead.phase is TransitPhase.APPROACHING
    assert ahead.score > score_contact(replace(ahead, phase=None))


def test_picks_cap_moon_and_slow_and_fall_back_to_personal_points_first() -> None:
    contacts = (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True),
        _contact(BodyName.MOON, BodyName.MOON, 0.0, exact_today=True, kind="square"),
        _contact(BodyName.MOON, BodyName.MARS, 0.0, exact_today=True, kind="sextile"),
        _contact(BodyName.SATURN, BodyName.VENUS, 0.0, exact_today=True),
        _contact(BodyName.PLUTO, BodyName.MERCURY, 0.1, exact_today=True),
        _contact(BodyName.MERCURY, BodyName.SUN, 1.0, peak_hour=None),
        _contact(BodyName.VENUS, BodyName.CHIRON, 0.0, exact_today=True),
    )
    picks = pick_daily_factors(contacts)
    ids = [item.id for item in picks]
    assert ids == ["saturn:trine:venus", "moon:square:moon", "moon:trine:sun"]  # tie: id order
    assert "pluto:trine:mercury" not in ids  # one slow slot (K-2)
    assert "moon:sextile:mars" not in ids  # two Moon picks at most (K-4)

    personal_second = (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True),
        _contact(BodyName.MERCURY, BodyName.SUN, 1.0, peak_hour=None),
        _contact(BodyName.VENUS, BodyName.CHIRON, 0.0, exact_today=True),
        _contact(BodyName.MARS, BodyName.TRUE_NODE, 0.0, exact_today=True),
    )
    # AS-11: a second contact on natal Sun comes before the thin points.
    assert [item.id for item in pick_daily_factors(personal_second)] == [
        "moon:trine:sun",
        "mercury:trine:sun",
        "mars:trine:true_node",  # Mars outweighs Venus among the thin points
    ]
    assert [item.id for item in pick_daily_factors(personal_second, allow_fallback=False)] == [
        "moon:trine:sun"
    ]


def test_slow_contact_perfecting_today_is_picked(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    saturn = engine.transiting_position(BodyName.SATURN, _local(START, 14), charts[3].config)
    chart = _move_natal(charts[3], BodyName.SUN, saturn.longitude)
    selection = select_daily_sky(engine, chart, START, include_trend_windows=False)
    slow = {item.id: item for item in selection.picks}.get("saturn:conjunction:sun")
    assert slow is not None and slow.exact_today and slow.tier is SkyTier.TREND
    assert slow is selection.picks[0]
    assert selection.tone is DayTone.HEAVY  # Saturn conjunct natal Sun (K-1)
    yesterday = select_daily_sky(
        engine, chart, START - timedelta(days=1), include_trend_windows=False
    )
    assert "saturn:conjunction:sun" not in {item.id for item in yesterday.picks}


def test_one_sky_event_on_two_aspected_natal_points_is_one_factor(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    day = START + timedelta(days=4)
    moon = engine.transiting_position(BodyName.MOON, _local(day, 10), charts[1].config)
    chart = _move_natal(charts[1], BodyName.SUN, moon.longitude)
    chart = _move_natal(chart, BodyName.VENUS, moon.longitude + 120.2)
    contacts = scan_day(engine, chart, day)
    ids = {item.id for item in contacts}
    merged = [item for item in contacts if item.merged]
    assert any(
        set(item.natal_points) >= {BodyName.SUN, BodyName.VENUS}
        and item.transit_body is BodyName.MOON
        for item in merged
    )
    # The partner is folded in, not listed twice.
    assert not {"moon:conjunction:sun", "moon:trine:venus"} <= ids


def test_south_node_relabel_and_generational_contacts_dropped(
    engine: NatalChartEngine,
    charts: tuple[NatalChart, ...],
    month: tuple[tuple[NatalChart, date, tuple[DayContact, ...]], ...],
) -> None:
    for _chart, _day, contacts in month:
        assert not any(
            item.transit_body in OUTER_BODIES and item.natal_body in OUTER_BODIES
            for item in contacts
        )
        assert not any(
            item.kind == "opposition"
            and item.natal_body in (BodyName.TRUE_NODE, BodyName.MEAN_NODE)
            for item in contacts
        )
    saturn = engine.transiting_position(BodyName.SATURN, _local(START, 12), charts[0].config)
    chart = _move_natal(charts[0], BodyName.TRUE_NODE, saturn.longitude + 180.0)
    selection = select_daily_sky(engine, chart, START)
    trend = {item.contact.id: item for item in selection.trend}
    south = trend["saturn:conjunction:south_node"]
    assert south.contact.natal_body is BodyName.SOUTH_NODE and south.contact.exact_angle == 0.0
    assert south.window is not None and south.window.start_date <= START <= south.window.end_date


@pytest.mark.parametrize(("hour", "minute"), [(23, 40), (0, 20), (3, 0)])
def test_moon_contact_belongs_to_the_vietnam_day_it_perfects(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...], hour: int, minute: int
) -> None:
    day = START + timedelta(days=5)
    exact_at = _local(day, hour, minute)
    moon = engine.transiting_position(BodyName.MOON, exact_at, charts[0].config)
    chart = _move_natal(charts[0], BodyName.SUN, moon.longitude)
    key = "moon:conjunction:sun"

    today = _find(scan_day(engine, chart, day), key)
    assert today.exact_today
    assert today.tier is SkyTier.TODAY
    assert today.time_kind is TimeKind.PEAKS_TODAY
    assert today.phase is TransitPhase.EXACT
    assert today.closest_at is not None and today.closest_at.date() == day
    assert abs(today.closest_at - exact_at) <= timedelta(minutes=5)
    assert today.min_orb < 0.05

    for neighbour in (day - timedelta(days=1), day + timedelta(days=1)):
        try:
            other: DayContact | None = _find(scan_day(engine, chart, neighbour), key)
        except KeyError:
            other = None
        assert other is None or (not other.exact_today and other.closest_at is None)


def test_moon_contact_entering_orb_before_midnight_belongs_to_the_day(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    # Orb ~limit + 0.13° at 23:30 and limit - 0.125° at midnight: it enters at ~23:45.
    day = START + timedelta(days=7)
    midnight = _local(day + timedelta(days=1), 0)
    config = charts[0].config
    limit = transit_orb_limit(BodyName.MOON, "conjunction")
    natal = engine.transiting_position(BodyName.MOON, midnight, config).longitude + limit - 0.125
    chart = _move_natal(charts[0], BodyName.SUN, natal)
    before = engine.transiting_position(BodyName.MOON, _local(day, 23, 30), config).longitude
    assert angular_distance(before, natal) > limit  # out of orb at the last in-day sample
    key = "moon:conjunction:sun"

    contact = _find(scan_day(engine, chart, day), key)
    assert contact.time_kind is TimeKind.STARTS_TODAY
    assert contact.closest_at is None and contact.phase is TransitPhase.APPROACHING
    assert _local(day, 23, 30) < contact.window_start < midnight
    assert contact.window_end == midnight
    entry = engine.transiting_position(BodyName.MOON, contact.window_start, config).longitude
    assert angular_distance(entry, natal) == pytest.approx(limit, abs=0.02)
    assert contact.min_orb == pytest.approx(limit - 0.125, abs=1e-3)
    # The next day carries it on from midnight.
    following = _find(scan_day(engine, chart, day + timedelta(days=1)), key)
    assert following.window_start == midnight


def test_moon_house_lookup_wraps_through_aries(charts: tuple[NatalChart, ...]) -> None:
    cusps = (20.0, 50.0, 80.0, 110.0, 140.0, 170.0, 200.0, 230.0, 260.0, 290.0, 320.0, 350.0)
    frame = HouseFrame.from_samples((CuspSample(cusps=cusps, ascendant=20.0, midheaven=290.0),))
    chart = charts[1]

    class FixedMoon(NatalChartEngine):
        def __init__(self, longitude: float) -> None:
            super().__init__()
            self.longitude = longitude

        def transiting_position(
            self, body: BodyName, observed_at: datetime, config: CalculationConfig | None = None
        ) -> BodyPosition:
            return BodyPosition(
                body=body,
                longitude=self.longitude,
                latitude=0.0,
                distance_au=0.0026,
                longitude_speed=13.0,
                retrograde=False,
                sign=sign_for_longitude(self.longitude),
                degree_in_sign=self.longitude % 30,
            )

    expected = {355.0: 12, 0.0: 12, 5.0: 12, 20.0: 1, 25.0: 1, 349.9: 11}
    for longitude, house in expected.items():
        context = moon_context(FixedMoon(longitude), chart, START, houses=frame)
        assert context.natal_house == house
        # No frame (no birthplace, or a time that cannot hold a house): no house.
        assert moon_context(FixedMoon(longitude), chart, START).natal_house is None
        assert context.observed_at == _local(START, 12)
        assert context.sign_change_at is None
        assert context.sign_at_start is context.sign_at_end is context.sign


def test_exact_time_moon_house_needs_proof_it_holds_over_the_time_error(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    # C2b: a typed HH:MM is not exact to the minute. The old selection read the house straight
    # from the stored cusps; now a house is only read from a frame that holds over the error.
    for chart in charts:
        for offset in range(3):
            assert moon_context(engine, chart, START + timedelta(days=offset)).natal_house is None


def test_moon_context_reports_the_sign_change_time(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    changes = 0
    for offset in range(6):
        day = START + timedelta(days=offset)
        context = moon_context(engine, charts[0], day)
        start, end = day_bounds(day)
        if context.sign_change_at is None:
            assert context.sign_at_start is context.sign_at_end
            continue
        changes += 1
        assert context.sign_at_start is not context.sign_at_end
        assert start <= context.sign_change_at < end
        before = engine.transiting_position(
            BodyName.MOON, context.sign_change_at - timedelta(minutes=1), charts[0].config
        )
        after = engine.transiting_position(
            BodyName.MOON, context.sign_change_at + timedelta(minutes=1), charts[0].config
        )
        assert (before.sign, after.sign) == (context.sign_at_start, context.sign_at_end)
    assert changes >= 2  # the Moon changes sign every ~2.5 days


def _window_chart(
    engine: NatalChartEngine,
    local_day: date,
    hour: int,
    precision: TimePrecision,
    zone: str = "Asia/Ho_Chi_Minh",
) -> NatalChart:
    """A synthetic chart stored the way the birth service stores a window midpoint."""

    stored = datetime.combine(local_day, time(hour), tzinfo=ZoneInfo(zone)).astimezone(UTC)
    chart = engine.calculate_chart(ChartInput(utc_datetime=stored, latitude=16.0, longitude=108.0))
    return chart.model_copy(update={"time_precision": precision})


@pytest.mark.parametrize(
    ("hour", "precision", "eligibility"),
    [
        (8, TimePrecision.APPROXIMATE, ContactEligibility.APPROXIMATE_TIME),
        (19, TimePrecision.APPROXIMATE, ContactEligibility.APPROXIMATE_TIME),
        (23, TimePrecision.APPROXIMATE, ContactEligibility.APPROXIMATE_NIGHT),
        (12, TimePrecision.UNKNOWN, ContactEligibility.DATE_ONLY),
    ],
)
def test_non_exact_birth_time_gets_interval_safe_contacts_without_houses(
    engine: NatalChartEngine,
    hour: int,
    precision: TimePrecision,
    eligibility: ContactEligibility,
) -> None:
    chart = _window_chart(engine, date(1990, 3, 14), hour, precision)
    assert chart.houses is not None  # houses on the record must still not be used
    domains = natal_domains(engine, chart)
    allowed = set(INTERVAL_NATAL_BODIES)
    if eligibility is ContactEligibility.APPROXIMATE_TIME:
        allowed.add(BodyName.MOON)
    assert set(domains) == allowed
    with_picks = 0
    for offset in range(10):
        day = START + timedelta(days=offset)
        selection = select_daily_sky(engine, chart, day, include_trend_windows=False)
        assert selection.eligibility is eligibility
        assert selection.moon.natal_house is None
        with_picks += bool(selection.picks)
        for item in (*selection.today, *selection.days, *selection.weeks):
            assert item.natal_body in allowed
            # In orb over the whole uncertain span: both domain ends, at the window's middle.
            middle = item.window_start + (item.window_end - item.window_start) / 2
            longitude = engine.transiting_position(
                item.transit_body, middle, chart.config
            ).longitude
            low, high = domains[item.natal_body]
            for natal in (low, high):
                assert (
                    abs(angular_distance(longitude, natal) - item.exact_angle)
                    <= item.orb_limit + 1e-6
                )
            extra = NATAL_MOON_WINDOW_EXTRA_ORB if item.natal_body is BodyName.MOON else 0.0
            assert item.orb_limit in {2.0 + extra, 2.5 + extra, 3.0 + extra}
    assert with_picks == 10


def test_night_window_covers_births_after_midnight_on_the_entered_date(
    engine: NatalChartEngine,
) -> None:
    # Born 03:00 on 14.03.1990 picks "Đêm"; the birth service stores 23:00 that date.
    birth_day = date(1990, 3, 14)
    night = _window_chart(engine, birth_day, 23, TimePrecision.APPROXIMATE)
    assert contact_eligibility(night) is ContactEligibility.APPROXIMATE_NIGHT
    domains = natal_domains(engine, night)
    assert BodyName.MOON not in domains
    date_only = natal_domains(engine, _window_chart(engine, birth_day, 12, TimePrecision.UNKNOWN))
    for hour in (0, 3, 6, 22, 23):
        at = datetime.combine(birth_day, time(hour), tzinfo=DAILY_TIMEZONE)
        for body, (low, high) in domains.items():
            assert isinstance(body, BodyName)  # no angle without an exact time (C2b)
            longitude = engine.transiting_position(body, at).longitude
            assert low - 1e-9 <= longitude <= high + 1e-9 or low <= longitude + 360.0 <= high
    for body, (low, high) in date_only.items():
        # The night domain contains the whole date-only domain.
        night_low, night_high = domains[body]
        shift = 360.0 if night_low > low + 180.0 else -360.0 if low > night_low + 180.0 else 0.0
        assert night_low <= low + shift + 1e-9 and high + shift <= night_high + 1e-9
    # Every daytime window keeps the narrow ±3 h rule.
    narrow = natal_domains(engine, _window_chart(engine, birth_day, 15, TimePrecision.APPROXIMATE))
    sun_low, sun_high = narrow[BodyName.SUN]
    night_sun_low, night_sun_high = domains[BodyName.SUN]
    assert sun_high - sun_low < 0.3 < 1.8 < night_sun_high - night_sun_low


def test_dawn_window_is_narrow_and_keeps_the_natal_moon(engine: NatalChartEngine) -> None:
    # "Rạng sáng 00-06h" (PL-37) is stored at 03:00, at most 3 h from its edges.
    dawn = _window_chart(engine, date(1990, 3, 14), 3, TimePrecision.APPROXIMATE)
    assert contact_eligibility(dawn) is ContactEligibility.APPROXIMATE_TIME
    domains = natal_domains(engine, dawn)
    assert BodyName.MOON in domains
    sun_low, sun_high = domains[BodyName.SUN]
    assert sun_high - sun_low < 0.3


def test_unrecognised_window_fails_closed_and_birth_zone_is_honoured(
    engine: NatalChartEngine,
) -> None:
    birth_day = date(1992, 8, 30)
    # Not on a stored midpoint in Vietnam time: treated as the wide night rule.
    odd = _window_chart(engine, birth_day, 10, TimePrecision.APPROXIMATE)
    assert contact_eligibility(odd) is ContactEligibility.APPROXIMATE_NIGHT
    # A foreign birthplace stored at its own 19:00 is recognised only with its zone.
    tokyo = _window_chart(engine, birth_day, 19, TimePrecision.APPROXIMATE, "Asia/Tokyo")
    assert contact_eligibility(tokyo) is ContactEligibility.APPROXIMATE_NIGHT
    assert (
        contact_eligibility(tokyo, birth_timezone="Asia/Tokyo")
        is ContactEligibility.APPROXIMATE_TIME
    )
    tokyo_night = _window_chart(engine, birth_day, 23, TimePrecision.APPROXIMATE, "Asia/Tokyo")
    assert (
        contact_eligibility(tokyo_night, birth_timezone="Asia/Tokyo")
        is ContactEligibility.APPROXIMATE_NIGHT
    )
    selection = select_daily_sky(
        engine, tokyo, START, include_trend_windows=False, birth_timezone="Asia/Tokyo"
    )
    assert selection.eligibility is ContactEligibility.APPROXIMATE_TIME
    # Exact and date-only charts ignore the window rule.
    exact = _window_chart(engine, birth_day, 10, TimePrecision.EXACT)
    assert contact_eligibility(exact) is ContactEligibility.EXACT_TIME


def test_birth_zone_reaches_the_scan_and_widens_the_natal_moon_limit(
    engine: NatalChartEngine,
) -> None:
    # A synthetic foreign birthplace stored at its own 19:00: the narrow window, natal Moon +1°.
    tokyo = _window_chart(engine, date(1992, 8, 30), 19, TimePrecision.APPROXIMATE, "Asia/Tokyo")
    domain = natal_domains(engine, tokyo, birth_timezone="Asia/Tokyo")[BodyName.MOON]
    centre = (domain[0] + domain[1]) / 2.0

    def ahead_of_centre(at: datetime) -> float:
        longitude = engine.transiting_position(BodyName.MOON, at, tokyo.config).longitude
        return (longitude - centre + 180.0) % 360.0 - 180.0

    day = next(
        START + timedelta(days=offset)
        for offset in range(30)
        if ahead_of_centre(_local(START + timedelta(days=offset), 0))
        < 0.0
        <= ahead_of_centre(_local(START + timedelta(days=offset + 1), 0))
    )
    selection = select_daily_sky(
        engine, tokyo, day, include_trend_windows=False, birth_timezone="Asia/Tokyo"
    )
    contact = _find(selection.today, "moon:conjunction:moon")
    expected = transit_orb_limit(BodyName.MOON, "conjunction") + NATAL_MOON_WINDOW_EXTRA_ORB
    assert contact.orb_limit == expected == 4.0
    # The in-day window is cut at the 4° worst-case orb, not the 3° night rule.
    start, end = _local(day, 0), _local(day + timedelta(days=1), 0)
    edges = [edge for edge in (contact.window_start, contact.window_end) if start < edge < end]
    assert edges
    for edge in edges:
        longitude = engine.transiting_position(BodyName.MOON, edge, tokyo.config).longitude
        assert worst_orb(longitude, domain, 0.0) == pytest.approx(expected, abs=0.05)


def test_worst_orb_is_the_interval_maximum() -> None:
    assert worst_orb(10.0, (130.0, 130.0), 120.0) == pytest.approx(0.0)
    assert worst_orb(10.0, (129.0, 131.0), 120.0) == pytest.approx(1.0)
    assert (
        worst_orb(10.0, (129.0, 131.0), 120.0) == orb_bounds((10.0, 10.0), (129.0, 131.0), 120.0)[1]
    )
    assert worst_orb(359.0, (358.0, 362.0), 0.0) == pytest.approx(3.0)


def test_jyotish_chart_stays_natal_only(engine: NatalChartEngine) -> None:
    born, lat, lon = SYNTHETIC_BIRTHS[2]
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=born, latitude=lat, longitude=lon),
        CalculationConfig.jyotish_recommended(),
    )
    selection = select_daily_sky(engine, chart, START)
    assert selection.eligibility is ContactEligibility.TRADITION_NOT_WESTERN
    assert not selection.picks and not selection.trend
    assert selection.tone is DayTone.MIXED


def test_day_tone_from_geometry() -> None:
    soft = (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True),
        _contact(BodyName.VENUS, BodyName.MOON, 0.0, exact_today=True, kind="sextile"),
        _contact(BodyName.MARS, BodyName.MARS, 1.0, peak_hour=None, kind="square"),
    )
    assert day_tone(soft, ()) is DayTone.LIGHT
    heavy_trend = (_contact(BodyName.SATURN, BodyName.MOON, 1.5, peak_hour=None, kind="square"),)
    assert day_tone(soft, heavy_trend) is DayTone.HEAVY
    jupiter_trend = (_contact(BodyName.JUPITER, BodyName.MOON, 1.5, peak_hour=None, kind="square"),)
    assert day_tone(soft, jupiter_trend) is DayTone.LIGHT
    hard = (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True, kind="square"),
        _contact(BodyName.MARS, BodyName.MOON, 0.0, exact_today=True, kind="square"),
    )
    assert day_tone(hard, ()) is DayTone.HEAVY
    moon_squares = (
        _contact(BodyName.MOON, BodyName.SUN, 0.0, exact_today=True, kind="square"),
        _contact(BodyName.MOON, BodyName.MARS, 0.0, exact_today=True, kind="square"),
    )
    assert day_tone(moon_squares, ()) is DayTone.MIXED
    assert day_tone((*soft[:1], *hard), ()) is DayTone.MIXED
    assert "tone" not in {field for field in DayContact.__dataclass_fields__}


def test_selection_is_versioned_and_deterministic(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    _, lat, lon = SYNTHETIC_BIRTHS[2]
    place = Birthplace(latitude=lat, longitude=lon)
    first = select_daily_sky(engine, charts[2], START, birthplace=place)
    assert first == select_daily_sky(engine, charts[2], START, birthplace=place)
    assert first.version == DAILY_SELECTION_VERSION == "daily-sky-selection-v3"
    assert first.timezone == "Asia/Ho_Chi_Minh"
    assert first.eligibility is ContactEligibility.EXACT_TIME
    assert first.moon.natal_house is not None
    assert first.houses is not None
    # Without the birthplace nothing proves a house holds over the birth-time error (C2b).
    blind = select_daily_sky(engine, charts[2], START)
    assert blind.moon.natal_house is None and blind.houses is None
    assert all(
        item.transit_house is None and item.natal_house is None and not item.ruled_houses
        for item in (*blind.today, *blind.days, *blind.weeks)
    )
    assert len(first.picks) == 3
    assert all(item.tier is SkyTier.TODAY for item in first.today)
    assert all(item.tier is SkyTier.DAYS for item in first.days)
    assert all(item.tier is SkyTier.WEEKS for item in first.weeks)
    assert all(item.contact.tier is SkyTier.TREND for item in first.trend)
    weights = [item.weight for item in first.trend]
    assert weights == sorted(weights, reverse=True)
    assert all(item.weight == trend_weight(item.contact) for item in first.trend)


def test_trend_weight_is_planet_times_aspect_times_target() -> None:
    pluto_sun = _contact(BodyName.PLUTO, BodyName.SUN, 1.0, peak_hour=None, kind="square")
    node_chiron = _contact(BodyName.TRUE_NODE, BodyName.CHIRON, 0.1, peak_hour=None, kind="sextile")
    assert trend_weight(pluto_sun) == 3.0 * 2.5 * 3.0
    assert trend_weight(node_chiron) == 1.0 * 1.5 * 1.0


def test_trend_windows_contain_today_and_their_closest_approaches(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    seen = 0
    for chart in charts:
        for item in select_daily_sky(engine, chart, START).trend:
            window = item.window
            assert window is not None
            assert window.start_date <= START <= window.end_date
            assert window.passes
            assert list(window.closest_dates) == sorted(window.closest_dates)
            assert all(window.start_date <= day <= window.end_date for day in window.closest_dates)
            assert isinstance(item.contact.natal_body, BodyName)  # no frame: no angle
            natal = chart.body(item.contact.natal_body).longitude
            for edge, open_edge, step in (
                (window.start_date, window.start_open, -1),
                (window.end_date, window.end_open, 1),
            ):
                for day, inside in ((edge, True), (edge + timedelta(days=step), False)):
                    # Today is in the window even when in orb for only part of it.
                    if (open_edge and not inside) or (inside and day == START):
                        continue
                    at = datetime.combine(day, time(12), tzinfo=DAILY_TIMEZONE)
                    position = engine.transiting_position(
                        item.contact.transit_body, at, chart.config
                    )
                    orb = abs(
                        angular_distance(position.longitude, natal) - item.contact.exact_angle
                    )
                    assert (orb <= item.contact.orb_limit) is inside
            for found in window.passes:
                at = datetime.combine(found.date, time(12), tzinfo=DAILY_TIMEZONE)
                position = engine.transiting_position(item.contact.transit_body, at, chart.config)
                orb = abs(angular_distance(position.longitude, natal) - item.contact.exact_angle)
                assert found.orb <= orb + 1e-6
                assert (found.kind is PassKind.EXACT) is (found.orb <= EXACT_ORB)
            seen += 1
    assert seen >= 4


def _saturn_station(engine: NatalChartEngine, after: date) -> date:
    day = after
    speed = engine.transiting_position(BodyName.SATURN, _local(day, 12)).longitude_speed
    while True:
        day += timedelta(days=1)
        current = engine.transiting_position(BodyName.SATURN, _local(day, 12)).longitude_speed
        if (current > 0) != (speed > 0) and current < 0:
            return day
        speed = current


def test_trend_window_bridges_retrograde_passes(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    station = _saturn_station(engine, START)
    station_longitude = engine.transiting_position(BodyName.SATURN, _local(station, 12)).longitude
    natal_longitude = station_longitude - 2.4  # Saturn leaves orb at the station, then returns
    first_pass = START
    while (
        abs(
            angular_distance(
                engine.transiting_position(BodyName.SATURN, _local(first_pass, 12)).longitude,
                natal_longitude,
            )
        )
        > 0.2
    ):
        first_pass += timedelta(days=1)
    chart = _move_natal(charts[3], BodyName.MARS, natal_longitude)
    contact = {item.id: item for item in scan_day(engine, chart, first_pass)}[
        "saturn:conjunction:mars"
    ]
    window = trend_window(engine, chart, contact, first_pass)
    assert not window.start_open and not window.end_open
    assert window.start_date < first_pass < station < window.end_date
    exact = [item for item in window.passes if item.kind is PassKind.EXACT]
    assert len(exact) == 3  # direct, retrograde, direct again (AS-2)
    assert abs((exact[0].date - first_pass).days) <= 1
    # The window really spans an out-of-orb gap around the station.
    gap = [
        day
        for day in (
            window.start_date + timedelta(days=offset)
            for offset in range((window.end_date - window.start_date).days)
        )
        if abs(
            angular_distance(
                engine.transiting_position(BodyName.SATURN, _local(day, 12)).longitude,
                natal_longitude,
            )
        )
        > contact.orb_limit
    ]
    assert gap and window.start_date < gap[0] < gap[-1] < window.end_date


def test_trend_window_finds_todays_exact_pass_and_flags_the_scan_bound(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    noon = _local(START, 12)
    saturn = engine.transiting_position(BodyName.SATURN, noon, charts[3].config)
    chart = _move_natal(charts[3], BodyName.MARS, saturn.longitude)
    contact = {item.id: item for item in scan_day(engine, chart, START)}["saturn:conjunction:mars"]
    assert contact.tier is SkyTier.TREND

    window = trend_window(engine, chart, contact, START)
    assert window.start_date < START < window.end_date
    assert not window.start_open and not window.end_open
    assert any(abs((day - START).days) <= 1 for day in window.closest_dates)
    assert any(item.kind is PassKind.EXACT for item in window.passes)

    bounded = trend_window(engine, chart, contact, START, max_scan_days=5)
    assert bounded.start_open and bounded.end_open
    assert (bounded.start_date, bounded.end_date) == (
        START - timedelta(days=5),
        START + timedelta(days=5),
    )
    assert bounded.closest_dates and START - timedelta(days=1) <= bounded.closest_dates[0]


def test_sampling_step_must_divide_the_day(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    with pytest.raises(ValueError, match="sample_minutes"):
        scan_day(engine, charts[0], START, sample_minutes=7)
