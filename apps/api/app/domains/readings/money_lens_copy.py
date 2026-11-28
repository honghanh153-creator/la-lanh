"""Copy of the money lens ("Góc Tiền bạc"), one set per sub-story (#710).

Design: ``docs/decisions/2026-11-25-goc-tien-bac-kien-truc.md``. The four sub-story codes are the
``money_situation`` values of that decision. Each has four sentences in ``copy_registry.json``:

``lens.money.<situation>.label``   the choice shown in the picker,
``lens.money.<situation>.note``    how the day shows up in that story,
``lens.money.<situation>.light``   a light thing to do (alone, within five minutes),
``lens.money.<situation>.action``  the normal small action.

A set is served whole or not at all: ``money_copy`` returns ``None`` until all four sentences of
a sub-story are approved. Nothing calls it at runtime yet; the request contract, storage and
consent of the lens are #711 and stay off until then.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.content.copy_approval import approved_copy
from app.domains.readings.lighter_action import within_five_minutes
from app.domains.readings.models import LIGHTER_ACTION_MAX_CHARS

MONEY_LENS_PREFIX = "lens.money."
MONEY_SITUATIONS = (
    "tuition_or_rent_shortfall",
    "month_end_shortfall",
    "family_remittance",
    "costly_social_invitation",
)
MONEY_COPY_PARTS = ("label", "note", "light", "action")


@dataclass(frozen=True, slots=True)
class MoneyCopy:
    label: str
    note: str
    light: str
    action: str


def money_copy_id(situation: str, part: str) -> str:
    """Registry id of one sentence; raises on an unknown sub-story or part."""

    if situation not in MONEY_SITUATIONS or part not in MONEY_COPY_PARTS:
        raise ValueError("unknown money copy entry")
    return f"{MONEY_LENS_PREFIX}{situation.replace('_', '-')}.{part}"


def money_copy(situation: str) -> MoneyCopy | None:
    """The approved set of ``situation``; ``None`` while any of its sentences is unserved."""

    texts = [approved_copy(money_copy_id(situation, part)) for part in MONEY_COPY_PARTS]
    if any(text is None for text in texts):
        return None
    label, note, light, action = (text for text in texts if text is not None)
    if len(light) > LIGHTER_ACTION_MAX_CHARS or not within_five_minutes(light):
        return None
    return MoneyCopy(label=label, note=note, light=light, action=action)
