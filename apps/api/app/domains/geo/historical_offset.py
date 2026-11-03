"""Historical UTC offset for a Vietnamese birth, by province and date.

Every Vietnamese place carries ``Asia/Ho_Chi_Minh``. tzdb models that zone on South
Vietnam's clocks; North Vietnam's history is kept in ``backzone`` as ``Asia/Hanoi`` and, for
1970 onward, mapped to ``Asia/Bangkok`` by ``zone1970.tab`` ("north Vietnam"):

- ``Asia/Ho_Chi_Minh``: +08 until 1955-07-01 01:00, +07, then +08 from 1959-12-31 23:00
  until 1975-06-13, +07 since.
- ``Asia/Hanoi``: +08 until "1954 Oct" (tzdb: day unspecified), +07 since, with no change in
  1960 or at unification. DRV Decision 121/CP (1967-08-08) only confirmed +07 from 1968-01-01.

So a birth north of the 1954 demarcation line (Bến Hải river) from October 1954 to
1 July 1955 and from 31 December 1959 23:00 to 13 June 1975 was on +07 while the zone says +08.
North provinces get +07 there. A province that straddles the line, an unclassified place, and
the unspecified switch month (October 1954) get no guess: the instant is the midpoint of both
candidates and is flagged ``offset_uncertain`` so callers treat the time as approximate.

Sources: https://github.com/eggert/tz (files ``asia``, ``backzone``, ``zone1970.tab``),
https://mm.icann.org/pipermail/tz/2020-June/029136.html,
https://mm.icann.org/pipermail/tz/2014-October/021654.html.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

VIETNAM_ZONE = "Asia/Ho_Chi_Minh"
NORTH_OFFSET = timedelta(hours=7)
SOUTH_OFFSET = timedelta(hours=8)
NORTH_RULE = "vn-north-utc7-v1"
UNCERTAIN_RULE = "vn-offset-uncertain-v1"

# Local wall-clock bounds. Before the start, Asia/Hanoi and Asia/Ho_Chi_Minh agree; from the
# end (unification) on, the whole country is on +07 in tzdb already.
_NORTH_SWITCH_MONTH = (datetime(1954, 10, 1), datetime(1954, 11, 1))
_DIVERGENCE_END = datetime(1975, 6, 13)

# Every current province (Resolution 202/2025/QH15) and former province entirely north of
# the Bến Hải river. Hà Tĩnh is the southernmost province fully on the north side.
NORTH_PLACE_IDS = frozenset(
    {
        "vn-hanoi",
        "vn-cao-bang",
        "vn-tuyen-quang",
        "vn-dien-bien",
        "vn-lai-chau",
        "vn-son-la",
        "vn-lao-cai",
        "vn-thai-nguyen",
        "vn-lang-son",
        "vn-quang-ninh",
        "vn-bac-ninh",
        "vn-phu-tho",
        "vn-hai-phong",
        "vn-hung-yen",
        "vn-ninh-binh",
        "vn-thanh-hoa",
        "vn-nghe-an",
        "vn-ha-tinh",
        "vn-former-ha-giang",
        "vn-former-yen-bai",
        "vn-former-bac-kan",
        "vn-former-vinh-phuc",
        "vn-former-hoa-binh",
        "vn-former-bac-giang",
        "vn-former-thai-binh",
        "vn-former-hai-duong",
        "vn-former-ha-nam",
        "vn-former-nam-dinh",
        "vn-former-quang-binh",
    }
)

# Merged Quảng Trị = former Quảng Bình (north) + former Quảng Trị, whose Vĩnh Linh district
# lay north of the Bến Hải river. A pick of "Quảng Trị" cannot tell which side.
SPLIT_PLACE_IDS = frozenset({"vn-quang-tri"})

SOUTH_PLACE_IDS = frozenset(
    {
        "vn-hue",
        "vn-da-nang",
        "vn-quang-ngai",
        "vn-gia-lai",
        "vn-khanh-hoa",
        "vn-dak-lak",
        "vn-lam-dong",
        "vn-dong-nai",
        "vn-ho-chi-minh",
        "vn-tay-ninh",
        "vn-dong-thap",
        "vn-vinh-long",
        "vn-an-giang",
        "vn-can-tho",
        "vn-ca-mau",
        "vn-former-quang-nam",
        "vn-former-kon-tum",
        "vn-former-binh-dinh",
        "vn-former-ninh-thuan",
        "vn-former-dak-nong",
        "vn-former-binh-thuan",
        "vn-former-phu-yen",
        "vn-former-binh-duong",
        "vn-former-ba-ria-vung-tau",
        "vn-former-binh-phuoc",
        "vn-former-long-an",
        "vn-former-hau-giang",
        "vn-former-soc-trang",
        "vn-former-ben-tre",
        "vn-former-tra-vinh",
        "vn-former-tien-giang",
        "vn-former-bac-lieu",
        "vn-former-kien-giang",
    }
)


@dataclass(frozen=True, slots=True)
class ResolvedBirthInstant:
    utc: datetime
    offset_uncertain: bool
    # None when the plain IANA zone applies; otherwise a versioned label that callers fold
    # into replay keys so a chart cached under the old offset is never served again.
    rule: str | None


def resolve_birth_instant(
    *, place_id: str, timezone_id: str, local: datetime
) -> ResolvedBirthInstant:
    """Convert a naive local birth time at a known place to UTC."""

    if local.tzinfo is not None:
        raise ValueError("local birth time must be naive wall-clock time")
    zoned = local.replace(tzinfo=ZoneInfo(timezone_id))
    plain = ResolvedBirthInstant(zoned.astimezone(UTC), offset_uncertain=False, rule=None)
    if (
        timezone_id != VIETNAM_ZONE
        or place_id in SOUTH_PLACE_IDS
        or not _NORTH_SWITCH_MONTH[0] <= local < _DIVERGENCE_END
        or zoned.utcoffset() == NORTH_OFFSET
    ):
        return plain
    if place_id in NORTH_PLACE_IDS and local >= _NORTH_SWITCH_MONTH[1]:
        north = local.replace(tzinfo=timezone(NORTH_OFFSET)).astimezone(UTC)
        return ResolvedBirthInstant(north, offset_uncertain=False, rule=NORTH_RULE)
    midpoint = local.replace(tzinfo=timezone((NORTH_OFFSET + SOUTH_OFFSET) / 2))
    return ResolvedBirthInstant(
        midpoint.astimezone(UTC), offset_uncertain=True, rule=UNCERTAIN_RULE
    )
