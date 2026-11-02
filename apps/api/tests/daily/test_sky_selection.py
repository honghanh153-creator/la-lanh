"""Daily v2 C2a: the day's sky factors in Vietnam time.

Every chart here is synthetic (made-up birth instants and coordinates), never a real person's.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.domains.astro.aspects import angular_distance
from app.domains.astro.engine import NatalChartEngine, sign_for_longitude
from app.domains.astro.models import (
    BodyName,
    BodyPosition,
    CalculationConfig,
    ChartInput,
    HousePosition,
    NatalChart,
    TimePrecision,
    TransitPhase,
)
from app.domains.daily.sky_selection import (
    DAILY_SELECTION_VERSION,
    DAILY_TIMEZONE,
    ContactEligibility,
    DayContact,
    SkyTier,
    moon_context,
    pick_daily_factors,
    scan_day,
    select_daily_sky,
    tier_for,
    trend_window,
)

SYNTHETIC_BIRTHS = (
    (datetime(1988, 6, 4, 3, 20, tzinfo=UTC), 16.05, 108.2),
    (datetime(1996, 11, 27, 14, 5, tzinfo=UTC), 10.8, 106.7),
    (datetime(2001, 2, 9, 22, 45, tzinfo=UTC), 20.86, 106.68),
    (datetime(1979, 9, 18, 8, 50, tzinfo=UTC), 12.25, 109.19),
)
START = date(2026, 11, 2)


@pytest.fixture(scope="module")
def engine() -> NatalChartEngine:
    return NatalChartEngine()


@pytest.fixture(scope="module")
def charts(engine: NatalChartEngine) -> tuple[NatalChart, ...]:
    return tuple(
        engine.calculate_chart(ChartInput(utc_datetime=born, latitude=lat, longitude=lon))
        for born, lat, lon in SYNTHETIC_BIRTHS
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
    return chart.model_copy(update={"bodies": moved})


def _local(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=DAILY_TIMEZONE)


def _contact(
    transit: BodyName,
    natal: BodyName,
    orb: float,
    *,
    exact_today: bool = False,
    kind: str = "trine",
) -> DayContact:
    return DayContact(
        id=f"{transit.value}:{kind}:{natal.value}",
        transit_body=transit,
        kind=kind,
        exact_angle=120.0,
        natal_body=natal,
        tier=tier_for(transit, exact_today=exact_today),
        min_orb=orb,
        orb_limit=2.5,
        closest_at=_local(START, 12),
        phase=TransitPhase.APPROACHING,
        exact_today=exact_today,
    )


@pytest.mark.parametrize(
    ("body", "exact_today", "tier"),
    [
        (BodyName.MOON, False, SkyTier.TODAY),
        (BodyName.MOON, True, SkyTier.TODAY),
        (BodyName.SUN, True, SkyTier.TODAY),
        (BodyName.MERCURY, False, SkyTier.DAYS),
        (BodyName.VENUS, False, SkyTier.DAYS),
        (BodyName.MARS, True, SkyTier.TODAY),
        (BodyName.JUPITER, True, SkyTier.TREND),
        (BodyName.SATURN, False, SkyTier.TREND),
        (BodyName.PLUTO, False, SkyTier.TREND),
        (BodyName.CHIRON, False, SkyTier.TREND),
        (BodyName.TRUE_NODE, True, SkyTier.TREND),
        (BodyName.MEAN_NODE, False, SkyTier.TREND),
    ],
)
def test_tier_follows_planet_speed(body: BodyName, exact_today: bool, tier: SkyTier) -> None:
    assert tier_for(body, exact_today=exact_today) is tier


def test_thirty_days_rotate_and_stay_diverse(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    repeats = comparisons = short_days = 0
    for chart in charts:
        previous: tuple[DayContact, ...] = ()
        for offset in range(30):
            contacts = scan_day(engine, chart, START + timedelta(days=offset))
            picks = pick_daily_factors(contacts)
            fast_natal = {item.natal_body for item in contacts if item.tier is not SkyTier.TREND}
            assert len(picks) == min(3, len(fast_natal))
            short_days += len(picks) < 3
            assert len({item.natal_body for item in picks}) == len(picks)
            assert all(item.tier is not SkyTier.TREND for item in picks)
            preferred = [item.preferred_natal for item in picks]
            assert preferred == sorted(preferred, reverse=True)  # fallbacks only fill the end
            if previous:
                comparisons += 1
                repeats += picks[0].id == previous[0].id
            previous = picks
    assert short_days == 0
    assert repeats / comparisons <= 0.10


def test_pick_ranks_exact_then_moon_then_orb_and_prefers_personal_points() -> None:
    contacts = (
        _contact(BodyName.VENUS, BodyName.SUN, 0.4),
        _contact(BodyName.MOON, BodyName.SUN, 1.5),
        _contact(BodyName.MERCURY, BodyName.VENUS, 0.1, exact_today=True),
        _contact(BodyName.MOON, BodyName.JUPITER, 0.0, exact_today=True),
        _contact(BodyName.MARS, BodyName.MARS, 2.0),
        _contact(BodyName.SATURN, BodyName.MOON, 0.0),
    )
    picks = pick_daily_factors(contacts)
    assert [item.id for item in picks] == [
        "mercury:trine:venus",
        "moon:trine:sun",
        "mars:trine:mars",
    ]
    only_two_personal = contacts[:4]
    assert [item.id for item in pick_daily_factors(only_two_personal)] == [
        "mercury:trine:venus",
        "moon:trine:sun",
        "moon:trine:jupiter",
    ]
    assert len(pick_daily_factors(only_two_personal, allow_fallback=False)) == 2


@pytest.mark.parametrize(("hour", "minute"), [(23, 40), (0, 20), (3, 0)])
def test_moon_contact_belongs_to_the_vietnam_day_it_perfects(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...], hour: int, minute: int
) -> None:
    day = START + timedelta(days=5)
    exact_at = _local(day, hour, minute)
    moon = engine.transiting_position(BodyName.MOON, exact_at, charts[0].config)
    chart = _move_natal(charts[0], BodyName.SUN, moon.longitude)
    key = "moon:conjunction:sun"

    today = {item.id: item for item in scan_day(engine, chart, day)}[key]
    assert today.exact_today
    assert today.tier is SkyTier.TODAY
    assert today.phase is TransitPhase.EXACT
    assert today.closest_at.date() == day
    assert abs(today.closest_at - exact_at) <= timedelta(minutes=5)
    assert today.min_orb < 0.05

    for neighbour in (day - timedelta(days=1), day + timedelta(days=1)):
        other = {item.id: item for item in scan_day(engine, chart, neighbour)}.get(key)
        assert other is None or not other.exact_today


def test_moon_house_lookup_wraps_through_aries(charts: tuple[NatalChart, ...]) -> None:
    cusps = (20.0, 50.0, 80.0, 110.0, 140.0, 170.0, 200.0, 230.0, 260.0, 290.0, 320.0, 350.0)
    houses = tuple(
        HousePosition(number=index, longitude=value, sign=sign_for_longitude(value))
        for index, value in enumerate(cusps, start=1)
    )
    chart = charts[1].model_copy(update={"houses": houses})

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
        context = moon_context(FixedMoon(longitude), chart, START)
        assert context.natal_house == house
        assert context.observed_at == _local(START, 12)


@pytest.mark.parametrize("precision", [TimePrecision.APPROXIMATE, TimePrecision.UNKNOWN])
def test_non_exact_birth_time_has_no_house_and_no_contacts(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...], precision: TimePrecision
) -> None:
    chart = charts[0].model_copy(update={"time_precision": precision})
    assert chart.houses is not None  # houses on the record must still not be used
    selection = select_daily_sky(engine, chart, START)
    assert selection.eligibility is ContactEligibility.TIME_NOT_EXACT
    assert selection.moon.natal_house is None
    assert selection.moon.sign is sign_for_longitude(selection.moon.longitude)
    assert selection.picks == selection.today == selection.days == ()
    assert not selection.trend


def test_jyotish_chart_gets_no_western_contacts(engine: NatalChartEngine) -> None:
    born, lat, lon = SYNTHETIC_BIRTHS[2]
    chart = engine.calculate_chart(
        ChartInput(utc_datetime=born, latitude=lat, longitude=lon),
        CalculationConfig.jyotish_recommended(),
    )
    selection = select_daily_sky(engine, chart, START)
    assert selection.eligibility is ContactEligibility.TRADITION_NOT_WESTERN
    assert not selection.picks
    assert not selection.trend


def test_selection_is_versioned_and_deterministic(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    first = select_daily_sky(engine, charts[2], START)
    assert first == select_daily_sky(engine, charts[2], START)
    assert first.version == DAILY_SELECTION_VERSION
    assert first.timezone == "Asia/Ho_Chi_Minh"
    assert first.eligibility is ContactEligibility.ELIGIBLE
    assert first.moon.natal_house is not None
    assert len(first.picks) == 3
    assert all(item.tier is SkyTier.TODAY for item in first.today)
    assert all(item.tier is SkyTier.DAYS for item in first.days)
    assert all(item.contact.tier is SkyTier.TREND for item in first.trend)


def test_trend_windows_contain_today_and_their_closest_approaches(
    engine: NatalChartEngine, charts: tuple[NatalChart, ...]
) -> None:
    seen = 0
    for chart in charts:
        for item in select_daily_sky(engine, chart, START).trend:
            window = item.window
            assert window is not None
            assert window.start_date <= START <= window.end_date
            assert window.closest_dates
            assert list(window.closest_dates) == sorted(window.closest_dates)
            assert all(window.start_date <= day <= window.end_date for day in window.closest_dates)
            natal = chart.body(item.contact.natal_body).longitude
            for edge, open_edge, step in (
                (window.start_date, window.start_open, -1),
                (window.end_date, window.end_open, 1),
            ):
                if open_edge:
                    continue
                outside = edge + timedelta(days=step)
                at = datetime.combine(outside, time(12), tzinfo=DAILY_TIMEZONE)
                position = engine.transiting_position(item.contact.transit_body, at, chart.config)
                orb = abs(angular_distance(position.longitude, natal) - item.contact.exact_angle)
                assert orb > item.contact.orb_limit
            seen += 1
    assert seen >= 4


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
