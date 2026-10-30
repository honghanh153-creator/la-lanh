"""Fixed rules of the human Tarot reader (US-24): one Vietnam day, 10 requests, release at 22:00.

The owner decided the limit and "no intake for tomorrow" (29/10/2026), then the 18:00 cut-off and
the 22:00 release, the retention below, monthly Sheet rotation, a service account on one file and a
Google Workspace account (30/10/2026, US-24 OD1-OD3, OD7).
"""

from __future__ import annotations

import secrets
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

PRODUCT_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
DAILY_LIMIT = 10
RELEASE_TIME = time(22, 0)
INTAKE_CLOSES = time(18, 0)
CONSENT_VERSION = "human-tarot-v1"
RESULT_SCHEMA = "human-tarot-result-v1"
READER = "owner"

# US-24 OD2, approved by the owner on 30/10/2026.
QUESTION_KEPT_AFTER_RELEASE = timedelta(hours=24)
RESULT_KEPT_AFTER_RELEASE = timedelta(days=30)
TOMBSTONE_KEPT = timedelta(days=2)
SLOT_KEPT_AFTER_DAY = timedelta(days=2)
DAY_TALLY_KEPT = timedelta(days=40)

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
REQUEST_CODE_PATTERN = r"^LL-[A-HJKMNP-Z2-9]{6}$"


def local_day(moment: datetime) -> date:
    return moment.astimezone(PRODUCT_TIMEZONE).date()


def local_at(day: date, at: time) -> datetime:
    return datetime.combine(day, at, tzinfo=PRODUCT_TIMEZONE)


def release_at(day: date) -> datetime:
    return local_at(day, RELEASE_TIME)


def day_end(day: date) -> datetime:
    """The first instant of the next Vietnam day."""

    return local_at(day + timedelta(days=1), time(0, 0))


def new_request_code() -> str:
    """A random job label for the owner's Sheet; it never grants access to anything."""

    return "LL-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
