"""The readable contract of a Hợp gu result (US-22 AC11), measured on what the page shows.

Used by the release audit (scripts/audit_radar_experience.py) on deterministic results and, since
Codex r55, by the rewrite gate on the assembled candidate before it can be published.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Astrology and app jargon allowed only in the "Xem thêm" layer.
JARGON = (
    "chart", "contact", "radar", "mood", "flirt", "chemistry", "synastry", "composite",
    "mặt trời", "mặt trăng", "sao thủy", "sao kim", "sao hỏa", "sao mộc", "sao thổ",
    "thiên vương", "hải vương", "diêm vương", "tam hợp", "lục hợp", "đối đỉnh", "đồng vị",
    "góc vuông", "nhà ", "cung ",
)  # fmt: skip

MAX_DEFAULT_WORDS = 400

_SENTENCE = re.compile(r"(?<=[.!?…])\s+")
_TRAILING = re.compile(r"[\s.!?…,;:]+$")


def normalize(text: str) -> str:
    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return _TRAILING.sub("", folded)


def default_view(result: dict[str, Any]) -> list[str]:
    """Text on screen before anything is opened: tier, reason, headline, areas, main sections."""

    signature = result["pair_signature"]
    texts = [signature["tier"]["label"], signature["summary"], signature["headline"]]
    if signature["tier"].get("score") is not None:
        texts.append(str(signature["tier"]["score"]))
    for area in signature["areas"]:
        texts += [area["label"], area["level_label"], area["note"]]
    for section in result["sections"]:
        if section["layer"] == "main":
            texts += [section["label"], section["title"], section["body"]]
            texts.append(section.get("question") or "")
    texts.append(result["disclaimer"])
    return [text for text in texts if text]


def more_layer(result: dict[str, Any]) -> list[str]:
    """Text behind the one "Xem thêm" disclosure."""

    texts: list[str] = []
    for section in result["sections"]:
        if section["layer"] != "more":
            continue
        texts += [section["label"], section["title"], section["body"]]
        for factor in section.get("factors") or []:
            texts += [factor["label"], factor["level_label"], factor["technical_note"]]
        for block in [*section["highlights"], *section["perspectives"]]:
            texts += [block["title"], block["body"]]
    return [text for text in texts if text]


def words(texts: list[str]) -> int:
    return sum(len(re.findall(r"[^\W_]+", text)) for text in texts)


def sentences(texts: list[str]) -> list[str]:
    return [
        normalize(part)
        for text in texts
        for part in _SENTENCE.split(text)
        if len(part.split()) >= 4
    ]


def readable_violations(result: dict[str, Any]) -> list[str]:
    """Closed codes for every AC11 rule the result breaks; empty when it reads as promised."""

    shown = default_view(result)
    found: list[str] = []
    if words(shown) > MAX_DEFAULT_WORDS:
        found.append("too_long")
    lowered = " ".join(shown).lower()
    if any(term in lowered for term in JARGON):
        found.append("jargon")
    every = sentences(shown + more_layer(result))
    if len(set(every)) != len(every):
        found.append("repeated_sentence")
    return found
