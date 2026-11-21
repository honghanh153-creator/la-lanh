"""Today's sky against a birth-date-only reader's Sun sign (US-21 AC07, #841 follow-up).

A birth date alone gives the Sun sign and nothing else the readings domain may use: the snapshot
keeps the sign, not the date, and no Moon, angle or house is read (AC08). Today's sky is public.
So a date-only Daily can still meet the day's transits by whole-sign aspect: a transiting body in
the sign a square away from the reader's Sun sign squares that Sun sign, whatever the exact birth
degree. A body counts only when it stays in one sign for the whole local day, so the contact holds
at every hour of the reader's day; the Moon (two and a half days per sign) is included on the days
it does. Nothing about the reader is calculated, stored or sent; only public positions are read.

Pure: the caller passes the positions at the start and the end of the local day.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.domains.astro.models import BodyPosition, ZodiacSign

SIGN_ORDER: tuple[str, ...] = tuple(sign.value for sign in ZodiacSign)
# Transiting bodies read against the Sun sign. The Sun itself (the reader's own birthday season)
# and the lunar node are left out: no Daily rule reads them.
SKY_BODIES: tuple[str, ...] = (
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "chiron",
)
# Whole-sign distance from the Sun sign to the transiting body's sign -> aspect kind.
DISTANCE_KINDS: dict[int, str] = {
    0: "conj",
    2: "coop",
    10: "coop",
    4: "coop",
    8: "coop",
    3: "tense",
    9: "tense",
    6: "tense",
}


def sky_contacts(
    sun_sign: str, start: Iterable[BodyPosition], end: Iterable[BodyPosition]
) -> tuple[str, ...]:
    """Codes ``"<body>:<kind>"`` of bodies in whole-sign aspect to ``sun_sign`` all day long."""

    if sun_sign not in SIGN_ORDER:
        raise ValueError("a sky contact needs a known Sun sign")
    first = {position.body.value: position.sign.value for position in start}
    last = {position.body.value: position.sign.value for position in end}
    contacts: list[str] = []
    for body in SKY_BODIES:
        sign = first.get(body)
        if sign is None or sign != last.get(body):
            continue  # not in one sign for the whole day: not certain for this reader's day
        distance = (SIGN_ORDER.index(sign) - SIGN_ORDER.index(sun_sign)) % 12
        kind = DISTANCE_KINDS.get(distance)
        if kind is not None:
            contacts.append(f"{body}:{kind}")
    return tuple(contacts)
