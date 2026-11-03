"""North/South Vietnam clock split, 1954-1975 (synthetic instants only, no personal data)."""

from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.domains.geo.historical_offset import (
    NORTH_PLACE_IDS,
    NORTH_RULE,
    SOUTH_PLACE_IDS,
    SPLIT_PLACE_IDS,
    UNCERTAIN_RULE,
    VIETNAM_ZONE,
    ResolvedBirthInstant,
    resolve_birth_instant,
)
from app.domains.geo.service import PLACE_BY_ID


def _resolve(place_id: str, local: datetime) -> ResolvedBirthInstant:
    return resolve_birth_instant(place_id=place_id, timezone_id=VIETNAM_ZONE, local=local)


def _at(local: datetime, hours: float) -> datetime:
    return local.replace(tzinfo=timezone(timedelta(hours=hours))).astimezone(UTC)


def test_every_catalog_place_is_classified_exactly_once() -> None:
    groups = (NORTH_PLACE_IDS, SOUTH_PLACE_IDS, SPLIT_PLACE_IDS)
    assert set().union(*groups) == set(PLACE_BY_ID)
    assert sum(len(group) for group in groups) == len(PLACE_BY_ID)
    assert all(place.timezone_id == VIETNAM_ZONE for place in PLACE_BY_ID.values())


def test_tzdb_still_puts_all_of_vietnam_on_the_southern_offset() -> None:
    # The premise of this module; if tzdb ever splits the zone, revisit the resolver.
    assert datetime(1965, 5, 1, tzinfo=ZoneInfo(VIETNAM_ZONE)).utcoffset() == timedelta(hours=8)


@pytest.mark.parametrize(
    "place_id",
    ["vn-hanoi", "vn-hai-phong", "vn-ha-tinh", "vn-former-quang-binh", "vn-former-nam-dinh"],
)
@pytest.mark.parametrize(
    "local",
    [
        datetime(1959, 12, 31, 23, 30),  # the hour the South skipped
        datetime(1960, 1, 1, 0, 0),
        datetime(1967, 12, 31, 12, 0),  # before Decision 121/CP's confirmation took effect
        datetime(1972, 7, 15, 6, 45),
        datetime(1975, 6, 12, 23, 59),
        datetime(1954, 11, 1, 0, 0),
        datetime(1955, 6, 30, 23, 0),
    ],
)
def test_north_uses_utc7_while_the_south_was_on_utc8(place_id: str, local: datetime) -> None:
    resolved = _resolve(place_id, local)
    assert resolved.utc == _at(local, 7)
    assert resolved.offset_uncertain is False
    assert resolved.rule in {NORTH_RULE, None}


def test_north_matches_tzdb_asia_bangkok_from_1970() -> None:
    # zone1970.tab maps "north Vietnam" to Asia/Bangkok.
    local = datetime(1971, 3, 9, 14, 20)
    expected = local.replace(tzinfo=ZoneInfo("Asia/Bangkok")).astimezone(UTC)
    assert _resolve("vn-hanoi", local).utc == expected


@pytest.mark.parametrize(
    "place_id", ["vn-hue", "vn-da-nang", "vn-ho-chi-minh", "vn-former-quang-nam"]
)
def test_south_keeps_the_iana_zone(place_id: str) -> None:
    local = datetime(1965, 5, 1, 8, 0)
    resolved = _resolve(place_id, local)
    assert resolved.utc == _at(local, 8)
    assert (resolved.offset_uncertain, resolved.rule) == (False, None)


@pytest.mark.parametrize(
    ("place_id", "local"),
    [
        ("vn-quang-tri", datetime(1965, 5, 1, 8, 0)),  # straddles the Bến Hải river
        ("vn-quang-tri", datetime(1955, 1, 10, 8, 0)),
        ("vn-hanoi", datetime(1954, 10, 15, 8, 0)),  # tzdb: switch day in Oct 1954 unknown
        ("vn-not-in-catalog", datetime(1965, 5, 1, 8, 0)),  # fail safe, never guess
    ],
)
def test_uncertain_offsets_use_the_midpoint_and_say_so(place_id: str, local: datetime) -> None:
    resolved = _resolve(place_id, local)
    assert resolved.utc == _at(local, 7.5)
    assert (resolved.offset_uncertain, resolved.rule) == (True, UNCERTAIN_RULE)


@pytest.mark.parametrize("place_id", ["vn-hanoi", "vn-quang-tri", "vn-ho-chi-minh"])
@pytest.mark.parametrize(
    ("local", "hours"),
    [
        (datetime(1950, 6, 1, 8, 0), 8),  # Asia/Hanoi and Asia/Ho_Chi_Minh agree
        (datetime(1957, 6, 1, 8, 0), 7),  # both on +07 between July 1955 and 1960
        (datetime(1975, 6, 13, 0, 30), 7),  # unification
        (datetime(1990, 6, 1, 8, 0), 7),
    ],
)
def test_outside_the_split_the_iana_zone_applies(
    place_id: str, local: datetime, hours: int
) -> None:
    resolved = _resolve(place_id, local)
    assert resolved.utc == _at(local, hours)
    assert (resolved.offset_uncertain, resolved.rule) == (False, None)


def test_other_zones_are_untouched() -> None:
    local = datetime(1965, 5, 1, 8, 0)
    resolved = resolve_birth_instant(place_id="vn-hanoi", timezone_id="Asia/Bangkok", local=local)
    assert (resolved.utc, resolved.rule) == (_at(local, 7), None)


def test_aware_local_time_is_refused() -> None:
    with pytest.raises(ValueError):
        _resolve("vn-hanoi", datetime(1965, 5, 1, 8, 0, tzinfo=UTC))
