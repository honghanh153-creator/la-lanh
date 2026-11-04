"""One slow transit, one episode: join the passes caused by retrograde motion (Daily v2 C2c).

A slow planet can meet the same natal point up to three times in one retrograde loop (direct,
retrograde, direct), and the outer planets more often over several loops. Between those passes
the contact may drop out of orb for weeks or months. Read day by day, each return looks like a
new event; this module returns the whole stretch as one ``TransitEpisode`` instead, with its
overall start and end, every in-orb segment, and every pass (AS-2, AS-16).

Rules (all deterministic for a chart, a contact and a date; geometry only, no copy, no
persistence, no logging):

* **Aspect point.** The contact is followed against one aspect point: the natal domain centre
  plus the aspect angle on the side the transiting body occupies today. A trine or sextile from
  the other side is a different episode, even under the same contact id.
* **Days.** A Vietnam civil day belongs to the episode when the contact is in orb at some moment
  of it (worst case over the natal domain, the measure ``scan_day`` uses), so every day the
  selection lists the contact lies in the same episode and the episode is the same whichever of
  those days asks. The signed separation is sampled at local midnights; between two samples it
  is monotone unless the body stations, and a station is located by bisection.
* **Joining.** After the contact leaves orb, the episode stays open only while the body could
  still come back by reversing: until it is farther from the aspect point than its largest
  reverse arc (``REVERSE_ARC_DEG``, measured) beyond the orb. A return inside that reach can
  only be a retrograde loop (or, for the true node, a direct wobble), so it joins; a later
  return is a new cycle. The Sun, the Moon and the mean node never reverse, so their episodes
  are a single segment.
* **Passes.** A pass is a closest approach inside the orb: either the exact crossing of the
  aspect point (``motion`` direct or retrograde) or a station that turns back short of it
  (``motion`` stationary, a near miss). Its ``orb`` is the worst case over the natal domain, so
  for a non-exact birth time a crossing of the domain centre can still be ``closest``.
* **Edges.** ``*_open`` means the scan bound (``max_scan_days``) was reached before that edge
  could be confirmed, so the true edge may lie further away. No pass is claimed beyond the scan,
  and an open episode may therefore carry no pass at all.
* **Key.** ``key`` (contact id and first in-orb day) is identical on every day of the episode,
  so later layers can treat all passes as one event. It is ``None`` when the start is open,
  because then the first day is not known.

Nothing in the request path calls this yet; the daily sky selection attaches an episode to each
trend contact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from itertools import pairwise

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import BodyName, NatalChart
from app.domains.daily.sky_selection import (
    DAILY_TIMEZONE,
    EXACT_ORB,
    MAX_SPEED_DEG_PER_DAY,
    SPEED_MARGIN,
    TREND_MIN_PROMINENCE,
    TREND_SCAN_DAYS,
    DayContact,
    NatalDomains,
    PassKind,
    _contact_domain,
)

TRANSIT_EPISODE_VERSION = "transit-episode-v1"
# Largest arc (°) a body travels against its usual direction between two stations, measured
# with the bundled ephemeris over 1900-2100 (planets: the retrograde arc; true node: its brief
# direct wobble). The Sun, the Moon and the mean node never reverse (0).
REVERSE_ARC_DEG = {
    BodyName.MERCURY: 16.31,
    BodyName.VENUS: 16.53,
    BodyName.MARS: 19.51,
    BodyName.JUPITER: 10.07,
    BodyName.SATURN: 6.97,
    BodyName.URANUS: 4.16,
    BodyName.NEPTUNE: 2.82,
    BodyName.PLUTO: 2.83,
    BodyName.CHIRON: 6.47,
    BodyName.TRUE_NODE: 0.12,
}
REVERSE_ARC_MARGIN_DEG = 0.5
# Shortest time (days) between two stations, measured the same way. Strides and jumps stay
# below it, so two sampled midnights are never more than one station apart; the true node's
# wobble can station twice in a day, so it is sampled daily and its passes are merged.
MIN_STATION_GAP_DAYS = {
    BodyName.MERCURY: 19,
    BodyName.VENUS: 40,
    BodyName.MARS: 60,
    BodyName.JUPITER: 117,
    BodyName.SATURN: 133,
    BodyName.URANUS: 149,
    BodyName.NEPTUNE: 156,
    BodyName.PLUTO: 156,
    BodyName.CHIRON: 128,
}
# In orb the scan strides by the days the body needs, at its largest speed, to move this far.
EPISODE_STRIDE_DEG = 2.0
MAX_STRIDE_DAYS = 30
# Bodies whose reversals are shorter than ``TREND_MIN_PROMINENCE`` (the true node's wobble):
# passes they make inside one wobble are one pass, as in ``sky_selection._passes``.
WOBBLE_BODIES = frozenset(
    body for body, arc in REVERSE_ARC_DEG.items() if arc < TREND_MIN_PROMINENCE
)
# Bisection stops below one minute.
_TOLERANCE_DAYS = 1.0 / 1440.0
_EPSILON = 1e-9


class PassMotion(StrEnum):
    DIRECT = "direct"
    RETROGRADE = "retrograde"
    STATIONARY = "stationary"


@dataclass(frozen=True, slots=True)
class EpisodePass:
    """One closest approach: an exact crossing, or a station turning back inside the orb."""

    at: datetime
    orb: float
    kind: PassKind
    motion: PassMotion

    @property
    def date(self) -> date:
        return self.at.date()


@dataclass(frozen=True, slots=True)
class EpisodeSegment:
    """Consecutive Vietnam days in orb."""

    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class TransitEpisode:
    """Every pass of one slow contact against one aspect point (see the module docstring)."""

    version: str
    contact_id: str
    transit_body: BodyName
    natal_body: BodyName
    kind: str
    start_date: date
    end_date: date
    start_open: bool
    end_open: bool
    segments: tuple[EpisodeSegment, ...]
    passes: tuple[EpisodePass, ...]

    @property
    def pass_count(self) -> int:
        return len(self.passes)

    @property
    def peak(self) -> EpisodePass | None:
        """The tightest pass (the earliest on a tie), or ``None`` when none was scanned."""

        if not self.passes:
            return None
        return min(self.passes, key=lambda item: (item.orb, item.at))

    @property
    def key(self) -> str | None:
        if self.start_open:
            return None
        return f"{self.contact_id}@{self.start_date.isoformat()}"

    def in_orb_on(self, day: date) -> bool:
        return any(item.start_date <= day <= item.end_date for item in self.segments)

    def passes_through(self, day: date) -> int:
        """How many passes fall on or before ``day``."""

        return sum(1 for item in self.passes if item.date <= day)


def _wrap(angle: float) -> float:
    """``angle`` in ``[-180, 180)``."""

    return (angle + 180.0) % 360.0 - 180.0


class _Track:
    """Signed separation from the aspect point, in days from local midnight of ``local_date``."""

    def __init__(
        self,
        engine: NatalChartEngine,
        chart: NatalChart,
        body: BodyName,
        point: float,
        local_date: date,
    ) -> None:
        self._engine = engine
        self._chart = chart
        self._body = body
        self._point = point
        self.origin = datetime.combine(local_date, time(), tzinfo=DAILY_TIMEZONE)
        # Integer keys are local midnights; bisection instants go to ``_probes``.
        self.midnights: dict[int, tuple[float, float]] = {}
        self._probes: dict[float, tuple[float, float]] = {}

    def _calculate(self, offset: float) -> tuple[float, float]:
        position = self._engine.transiting_position(
            self._body, self.origin + timedelta(days=offset), self._chart.config
        )
        return _wrap(position.longitude - self._point), position.longitude_speed

    def midnight(self, day: int) -> tuple[float, float]:
        if day not in self.midnights:
            self.midnights[day] = self._calculate(float(day))
        return self.midnights[day]

    def at(self, offset: float) -> tuple[float, float]:
        if offset == int(offset):
            return self.midnight(int(offset))
        if offset not in self._probes:
            self._probes[offset] = self._calculate(offset)
        return self._probes[offset]

    def peak_between(self, left: float, right: float) -> float:
        """Largest |separation| sampled strictly between two instants (0 when none)."""

        values = [
            abs(value[0])
            for samples in (self.midnights, self._probes)
            for offset, value in samples.items()
            if left < offset < right
        ]
        return max(values, default=0.0)

    def station(self, left: float, right: float) -> float | None:
        """The station between two instants whose speeds differ in sign (at most one there)."""

        forward = self.at(left)[1] > 0
        if (self.at(right)[1] > 0) == forward:
            return None
        while right - left > _TOLERANCE_DAYS:
            middle = (left + right) / 2.0
            if (self.at(middle)[1] > 0) == forward:
                left = middle
            else:
                right = middle
        return (left + right) / 2.0

    def crossing(self, left: float, right: float) -> float:
        """Where the separation changes sign between two instants (monotone there)."""

        positive = self.at(left)[0] >= 0
        while right - left > _TOLERANCE_DAYS:
            middle = (left + right) / 2.0
            if (self.at(middle)[0] >= 0) == positive:
                left = middle
            else:
                right = middle
        return (left + right) / 2.0

    def day_min(self, day: int) -> float:
        """Smallest |separation| during the local day ``day``."""

        first, _ = self.midnight(day)
        last, _ = self.midnight(day + 1)
        if (first >= 0) != (last >= 0):
            return 0.0
        station = self.station(float(day), float(day + 1))
        if station is not None:
            turn = self.at(station)[0]
            if (turn >= 0) != (first >= 0):
                return 0.0
            return min(abs(first), abs(last), abs(turn))
        return min(abs(first), abs(last))


def _aspect_point(
    engine: NatalChartEngine, chart: NatalChart, contact: DayContact, centre: float
) -> float:
    if contact.exact_angle in (0.0, 180.0):
        return (centre + contact.exact_angle) % 360.0
    # The side the body occupies while in orb today.
    middle = contact.window_start + (contact.window_end - contact.window_start) / 2
    longitude = engine.transiting_position(contact.transit_body, middle, chart.config).longitude
    side = 1.0 if _wrap(longitude - centre) >= 0 else -1.0
    return (centre + side * contact.exact_angle) % 360.0


def episode_stride(body: BodyName) -> int:
    """In-orb scan stride in days (daily for the wobbling true node)."""

    if body in WOBBLE_BODIES:
        return 1
    speed = MAX_SPEED_DEG_PER_DAY.get(body, 1.0) * SPEED_MARGIN
    return max(1, min(MAX_STRIDE_DAYS, int(EPISODE_STRIDE_DEG / speed)))


def trend_episode(
    engine: NatalChartEngine,
    chart: NatalChart,
    contact: DayContact,
    local_date: date,
    *,
    max_scan_days: int = TREND_SCAN_DAYS,
    domains: NatalDomains | None = None,
    birth_timezone: str | None = None,
) -> TransitEpisode:
    """The episode that contains ``local_date`` for a contact in orb on that day.

    ``contact`` comes from ``scan_day`` for ``local_date``; the day belongs to the episode by
    construction. ``max_scan_days`` bounds the scan on each side.
    """

    if max_scan_days < 1:
        raise ValueError("max_scan_days must be at least 1")
    low, high = _contact_domain(engine, chart, contact, domains, birth_timezone)
    half_width = (high - low) / 2.0
    reach = contact.orb_limit - half_width
    if reach < 0:
        raise ValueError("the natal domain is wider than the orb")
    point = _aspect_point(engine, chart, contact, (low + half_width) % 360.0)
    track = _Track(engine, chart, contact.transit_body, point, local_date)
    speed = MAX_SPEED_DEG_PER_DAY.get(contact.transit_body, 1.0) * SPEED_MARGIN
    stride = episode_stride(contact.transit_body)
    give_up = reach + REVERSE_ARC_DEG.get(contact.transit_body, 0.0) + REVERSE_ARC_MARGIN_DEG

    def inside(day: int) -> bool:
        return day == 0 or track.day_min(day) <= reach + _EPSILON

    def all_inside(direction: int, near: int, far: int) -> bool:
        """Whether every day between two in-orb days ``near`` and ``far`` is in orb.

        On a stretch without a station the separation is monotone, so the in-orb instants form
        one interval; with one station, each side of it is monotone and the station itself must
        be in orb as well.
        """

        first, last = (near, far + 1) if direction > 0 else (-far, -near + 1)
        station = track.station(float(first), float(last))
        return station is None or abs(track.at(station)[0]) <= reach + _EPSILON

    def scan(direction: int) -> tuple[int, bool, list[tuple[int, int]]]:
        """Last in-orb day count on one side, whether it is open, and the gaps (as counts)."""

        last_in = 0
        gaps: list[tuple[int, int]] = []
        while True:
            # In orb at ``last_in``: stride while every day in between stays in orb.
            far = last_in + stride
            if (
                far <= max_scan_days
                and inside(direction * far)
                and all_inside(direction, last_in, far)
            ):
                last_in = far
                continue
            exit_day = None
            for day in range(last_in + 1, min(far, max_scan_days) + 1):
                if not inside(direction * day):
                    exit_day = day
                    break
                last_in = day
            if exit_day is None:
                if last_in >= max_scan_days:
                    return last_in, True, gaps
                continue
            # Out of orb: jump while the body cannot be back, stop once it cannot come back.
            day = exit_day
            while True:
                separation = track.day_min(direction * day)
                if separation > give_up:
                    return last_in, False, gaps
                step = max(1, math.floor((separation - reach) / speed))
                if day + step > max_scan_days:
                    return last_in, True, gaps
                day += step
                if inside(direction * day):
                    gaps.append((exit_day, day - 1))
                    last_in = day
                    break

    back, start_open, back_gaps = scan(-1)
    ahead, end_open, ahead_gaps = scan(1)
    start, end = -back, ahead
    gaps = sorted([(-last, -first) for first, last in back_gaps] + ahead_gaps)
    segments: list[tuple[int, int]] = []
    cursor = start
    for first, last in gaps:
        segments.append((cursor, first - 1))
        cursor = last + 1
    segments.append((cursor, end))

    def local(offset: float) -> datetime:
        return (track.origin + timedelta(days=offset)).replace(second=0, microsecond=0)

    found = _passes(track, start, end + 1, reach)
    if contact.transit_body in WOBBLE_BODIES:
        found = _merge_wobbles(track, found)
    passes = [
        EpisodePass(
            at=local(offset),
            orb=round(orb + half_width, 4),
            kind=PassKind.EXACT if orb + half_width <= EXACT_ORB else PassKind.CLOSEST,
            motion=motion,
        )
        for offset, orb, motion in found
    ]
    return TransitEpisode(
        version=TRANSIT_EPISODE_VERSION,
        contact_id=contact.id,
        transit_body=contact.transit_body,
        natal_body=contact.natal_body,
        kind=contact.kind,
        start_date=local_date + timedelta(days=start),
        end_date=local_date + timedelta(days=end),
        start_open=start_open,
        end_open=end_open,
        segments=tuple(
            EpisodeSegment(
                start_date=local_date + timedelta(days=first),
                end_date=local_date + timedelta(days=last),
            )
            for first, last in segments
        ),
        passes=tuple(passes),
    )


def _passes(
    track: _Track, first: int, last: int, reach: float
) -> list[tuple[float, float, PassMotion]]:
    """``(offset, |separation|, motion)`` of each pass between two midnights, in time order.

    Consecutive sampled midnights are at most one station apart (strides and jumps are far
    shorter than the time between two stations), and the separation is monotone on each side
    of that station, so every crossing and near miss is found between them.
    """

    found: list[tuple[float, float, PassMotion]] = []
    days = sorted(day for day in track.midnights if first <= day <= last)
    for left, right in pairwise(days):
        station = track.station(float(left), float(right))
        pieces = (
            [(float(left), station), (station, float(right))]
            if station is not None
            else [(float(left), float(right))]
        )
        crossed = False
        for start, end in pieces:
            if (track.at(start)[0] >= 0) != (track.at(end)[0] >= 0):
                crossed = True
                at = track.crossing(start, end)
                motion = PassMotion.DIRECT if track.at(at)[1] > 0 else PassMotion.RETROGRADE
                found.append((at, abs(track.at(at)[0]), motion))
        if station is None or crossed:
            continue
        turn = abs(track.at(station)[0])
        if turn <= reach + _EPSILON and turn <= min(
            abs(track.at(float(left))[0]), abs(track.at(float(right))[0])
        ):
            found.append((station, turn, PassMotion.STATIONARY))
    return found


def _merge_wobbles(
    track: _Track, found: list[tuple[float, float, PassMotion]]
) -> list[tuple[float, float, PassMotion]]:
    """Keep one pass per wobble: neighbours count separately only past ``TREND_MIN_PROMINENCE``."""

    kept = list(found)
    merged = True
    while merged and len(kept) > 1:
        merged = False
        for index in range(len(kept) - 1):
            first, second = kept[index], kept[index + 1]
            peak = track.peak_between(first[0], second[0])
            if peak - max(first[1], second[1]) < TREND_MIN_PROMINENCE:
                kept.remove(second if second[1] >= first[1] else first)
                merged = True
                break
    return kept
