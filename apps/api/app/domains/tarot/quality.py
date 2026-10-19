"""Deterministic checks for known unsafe claims, not a semantic quality guarantee."""

import re
import unicodedata

from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import TarotReading


def _fold(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(char) != "Mn"
    ).replace("đ", "d")


_UNSAFE = tuple(
    re.compile(pattern)
    for pattern in (
        r"(?<!khong )(?<!chua )\bchac chan\b",
        r"(?<!\d)100\s*%",
        r"\b(?:nguoi kia|nguoi ay|ho) (?:dang |that su |rat )?"
        r"(?:yeu|thich|muon quay lai voi|dang nghi ve) ban\b",
        r"\b(?:nguoi kia|nguoi ay|ho) (?:dang |that su |rat )?"
        r"(?:nho|mong|doi|cho|ghet|het yeu|chan) ban\b",
        r"\b(?:nguoi kia|nguoi ay|ho) (?:dang |that su |rat )?"
        r"(?:cho|doi) (?:ban|tin nhan|loi nhan)\b",
        r"\bthao tung\b",
        r"\b(?:lam|khien) (?:ho|nguoi kia|nguoi ay) ghen\b",
        r"\b(?:ngung|bo|dung) (?:uong )?thuoc\b",
        r"\b(?:ban mac|ban bi) (?:tram cam|roi loan|benh)\b",
        r"\b(?:ngay mai|tuan toi|thang toi).{0,60}\bban se\b.{0,60}"
        r"(?:nhan duoc|ket hon|quay lai|trung|thanh cong)",
    )
)


def prose_is_safe(reading: TarotReading) -> bool:
    values = [reading.headline, reading.summary, reading.closing_prompt]
    values.extend(
        value
        for position in reading.positions
        for value in (
            position.meaning_here,
            position.everyday_scene,
            position.reflection_question,
            position.small_action or "",
        )
    )
    text = _fold(" ".join(values))
    if any(pattern.search(text) for pattern in _UNSAFE):
        return False
    selected = {position.card.id for position in reading.positions}
    for card in all_cards():
        if card.id in selected:
            continue
        for title in (card.title_vi, card.title_en):
            # Words such as "world" also have ordinary meanings. Reject an extra
            # card attribution rather than every occurrence of its common name.
            attribution = (
                r"(?<!\w)"
                + re.escape(_fold(title))
                + r"(?!\w)\s*(?::|\b(?:cho thay|goi|nhac|noi ve|o vi tri|la la bai)\b)"
            )
            if re.search(attribution, text):
                return False
    return True
