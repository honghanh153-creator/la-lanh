"""Synthetic reader personas for the layer-C content gate (Daily v2 plan, section 1.1, rule N-3).

Every sentence about a life theme must read true, and must not hurt, for all four people below.
They are invented test fixtures: no real person, no birth date, no birth place. They are never
used to select or personalise a reading. Lá Lành does not ask, infer or store a reader's
relationship status, whether they have children or whether they hope to (rule N-7); the gate
reads these flags only to imagine who might be reading.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgeBand(StrEnum):
    YOUNG_ADULT = "young_adult"
    MIDLIFE = "midlife"
    OLDER = "older"


@dataclass(frozen=True)
class ReaderPersona:
    key: str
    description: str
    age_band: AgeBand
    has_partner: bool
    has_children: bool
    children_grown: bool
    hoping_for_child: bool
    # Keys from ``house_meanings.HOUSE_MEANINGS`` that would hurt this reader if a sentence
    # stated or assumed them on their own (the judge checks these never stand alone).
    tender_meaning_keys: tuple[str, ...]


READER_PERSONAS: tuple[ReaderPersona, ...] = (
    ReaderPersona(
        key="single_no_children",
        description="Sống một mình, chưa có người yêu, chưa có con, đang bận lo cho công việc.",
        age_band=AgeBand.YOUNG_ADULT,
        has_partner=False,
        has_children=False,
        children_grown=False,
        hoping_for_child=False,
        tender_meaning_keys=("marriage", "in_laws", "children"),
    ),
    ReaderPersona(
        key="married_with_children",
        description="Đã lập gia đình, có con nhỏ, ngày nào cũng chia mình cho nhà và việc làm.",
        age_band=AgeBand.MIDLIFE,
        has_partner=True,
        has_children=True,
        children_grown=False,
        hoping_for_child=False,
        tender_meaning_keys=("romance",),
    ),
    ReaderPersona(
        key="hoping_for_child",
        description="Có bạn đời, đã mong con nhiều năm mà chưa có, nhạy cảm với chuyện con cái.",
        age_band=AgeBand.MIDLIFE,
        has_partner=True,
        has_children=False,
        children_grown=False,
        hoping_for_child=True,
        tender_meaning_keys=("children", "parents_home", "in_laws"),
    ),
    ReaderPersona(
        key="older_grown_children",
        description="Đã lớn tuổi, con cái đã trưởng thành và ở xa, có thời gian cho mình hơn.",
        age_band=AgeBand.OLDER,
        has_partner=True,
        has_children=True,
        children_grown=True,
        hoping_for_child=False,
        tender_meaning_keys=("children", "romance", "parents_home", "parent_public"),
    ),
)
