"""Fail a release when Hợp gu works technically but reads like generic, hard or unsafe filler.

Two layers (renderer ``radar-readable-v2``, owner feedback 29/10/2026, research report Phần B,
"Cách đo"):

1. One fixed pair x 4 contexts x 4 voices: the practice actions are evidence-bound and distinct,
   the context changes the real-life suggestion, the voice changes delivery, nothing raw leaks.
2. The 50 synthetic pairs of ``radar-pairs-v1`` x crush/friend/partner/someone: the readable
   contract, measured on what the page shows before anything is opened (the "default view").
   Thresholds below are the release gate; each one is recorded in US-22 (AC11) and the review
   ``docs/reviews/2026-10-29-hop-gu-readable.md``.

The tier reference distribution is also regenerated and compared with ``reading.TIER_REFERENCE``.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import ChartInput, RelationshipBundle
from app.domains.radar import reading
from app.domains.radar.reading import build_radar_reading
from app.domains.relationships.models import RelationshipVoice
from scripts.radar_tier_reference import reference_signals
from scripts.radar_tier_reference import report as reference_report
from scripts.variety_baseline import _SENTENCE, _radar_chart, normalize

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/variety/radar-pairs-v1.json"
CONTEXTS = ("crush", "friend", "partner", "someone")
COMPARED_CONTEXTS = ("crush", "friend", "partner")

# Unsafe or judgemental wording anywhere a reader can see (both layers). "thử lòng" is left to
# the rewrite gate: an approved editorial prompt says "thay vì thử lòng" (instead of testing).
FORBIDDEN = (
    "soulmate", "red flag", "cờ đỏ", "toxic", "chắc chắn", "định mệnh", "tri kỷ",
    "người kia nghĩ", "người kia đang nghĩ", "người kia cảm thấy", "người kia muốn",
    "người kia sẽ", "người kia thích", "họ nghĩ", "họ đang nghĩ", "họ cảm thấy", "họ muốn",
    "họ thích", "thích bạn", "yêu bạn", "theo dõi", "tỷ lệ", "tỉ lệ", "%", "/100",
    "hai nhu cầu bật lên", "cross-aspect", "jyotish", "sau mutual", "a→b",
)  # fmt: skip
# Astrology and app jargon allowed only in the "Xem thêm" layer.
JARGON = (
    "chart", "contact", "radar", "mood", "flirt", "chemistry", "synastry", "composite",
    "mặt trời", "mặt trăng", "sao thủy", "sao kim", "sao hỏa", "sao mộc", "sao thổ",
    "thiên vương", "hải vương", "diêm vương", "tam hợp", "lục hợp", "đối đỉnh", "đồng vị",
    "góc vuông", "nhà ", "cung ",
)  # fmt: skip

MAX_DEFAULT_WORDS = 400
MAX_TENSION_SHARE = 0.6
MAX_TIER_SHARE = 0.4
MIN_CONTEXT_CHANGE = 0.5


def _fixed_bundle() -> RelationshipBundle:
    engine = NatalChartEngine()
    first = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1990, 1, 1, 5, 15, tzinfo=UTC),
            latitude=21.0285,
            longitude=105.8542,
        )
    )
    second = engine.calculate_chart(
        ChartInput(
            utc_datetime=datetime(1992, 7, 21, 12, 40, tzinfo=UTC),
            latitude=10.8231,
            longitude=106.6297,
        )
    )
    return engine.calculate_relationship_bundle(first, second)


def _section(result: dict[str, Any], key: str) -> dict[str, Any] | None:
    return next((item for item in result["sections"] if item["key"] == key), None)


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


def _fixed_pair_gate() -> None:
    bundle = _fixed_bundle()
    context_checks: set[str] = set()
    voice_actions: set[str] = set()
    for context in CONTEXTS:
        for voice in RelationshipVoice:
            result = build_radar_reading(bundle, context=context, voice=voice)
            practice = _section(result, "practice")
            check = _section(result, "check")
            if practice is None or not practice["highlights"] or check is None:
                raise SystemExit(f"experience gate: {context}/{voice} has no useful action")
            actions = practice["highlights"]
            disclosed = {item["evidence_id"] for item in practice["evidence"]}
            if any(not set(item["evidence_ids"]) <= disclosed for item in actions):
                raise SystemExit(f"experience gate: {context}/{voice} action lacks evidence")
            if [item["concept_id"] for item in actions] != result["metadata"]["concept_ids"]:
                raise SystemExit(f"experience gate: {context}/{voice} concept trace mismatch")
            if len({item["body"] for item in actions}) != len(actions):
                raise SystemExit(f"experience gate: {context}/{voice} repeats an action")
            serialized = json.dumps(result, ensure_ascii=False)
            if any(raw in serialized for raw in ("1990", "1992", "21.0285", "106.6297")):
                raise SystemExit("experience gate: raw birth data reached the public projection")
            context_checks.add(check["body"])
            if context == "crush":
                voice_actions.add("|".join(item["body"] for item in actions))
    if len(context_checks) != len(CONTEXTS):
        raise SystemExit("experience gate: context does not change the real-life suggestion")
    if len(voice_actions) != len(RelationshipVoice):
        raise SystemExit("experience gate: voice choice does not materially change delivery")


def readable_report() -> dict[str, Any]:
    engine = NatalChartEngine()
    pairs = json.loads(FIXTURES.read_text())["pairs"]
    readings: dict[tuple[str, str], dict[str, Any]] = {}
    for pair in pairs:
        bundle = engine.calculate_relationship_bundle(
            _radar_chart(engine, pair["a"]), _radar_chart(engine, pair["b"])
        )
        for context in CONTEXTS:
            readings[(pair["id"], context)] = build_radar_reading(
                bundle, context=context, voice=RelationshipVoice.STRAIGHT_WARM
            )
    results = list(readings.values())
    default_words = [words(default_view(result)) for result in results]
    tiers = Counter(
        readings[(pair["id"], "someone")]["pair_signature"]["tier"]["key"] for pair in pairs
    )
    changes = []
    for pair in pairs:
        for left, right in combinations(COMPARED_CONTEXTS, 2):
            a = set(sentences(default_view(readings[(pair["id"], left)])))
            b = set(sentences(default_view(readings[(pair["id"], right)])))
            changes.append(len(a - b) / len(a) if a else 0.0)
    return {
        "readings": len(results),
        "default_words": {
            "min": min(default_words),
            "median": statistics.median(default_words),
            "max": max(default_words),
        },
        "default_plus_why_words_median": statistics.median(
            words(default_view(result))
            + words(
                [
                    factor["technical_note"]
                    for factor in (_section(result, "why") or {}).get("factors", [])
                ]
            )
            for result in results
        ),
        "headlines_with_nhung": sum("nhưng" in r["headline"].lower() for r in results),
        "kicker_not_tier_label": sum(
            r["pair_signature"]["kicker"] != r["pair_signature"]["tier"]["label"] for r in results
        ),
        "jargon_in_default_view": sum(
            term in " ".join(default_view(r)).lower() for r in results for term in JARGON
        ),
        "forbidden_anywhere": sum(
            term in " ".join(default_view(r) + more_layer(r)).lower()
            for r in results
            for term in FORBIDDEN
        ),
        "repeated_sentences": sum(
            len(found) - len(set(found))
            for found in (sentences(default_view(r) + more_layer(r)) for r in results)
        ),
        "tension_share": round(
            sum(_section(r, "friction") is not None for r in results) / len(results), 3
        ),
        "tier_share_50_pairs": {
            key: round(tiers[key] / len(pairs), 2) for key, _ in reading.TIER_BANDS
        },
        "context_change_default_view": round(statistics.fmean(changes), 3),
    }


def readable_failures(report: dict[str, Any]) -> list[str]:
    failures = []
    if report["default_words"]["max"] > MAX_DEFAULT_WORDS:
        failures.append(f"default view over {MAX_DEFAULT_WORDS} words")
    for key in (
        "headlines_with_nhung",
        "kicker_not_tier_label",
        "jargon_in_default_view",
        "forbidden_anywhere",
        "repeated_sentences",
    ):
        if report[key]:
            failures.append(f"{key} = {report[key]}")
    if not 0 < report["tension_share"] <= MAX_TENSION_SHARE:
        failures.append(f"tension share {report['tension_share']} not in (0, {MAX_TENSION_SHARE}]")
    if max(report["tier_share_50_pairs"].values()) > MAX_TIER_SHARE:
        failures.append(f"one tier holds more than {MAX_TIER_SHARE} of the pairs")
    if report["context_change_default_view"] < MIN_CONTEXT_CHANGE:
        failures.append(
            f"context change {report['context_change_default_view']} < {MIN_CONTEXT_CHANGE}"
        )
    return failures


def audit() -> None:
    _fixed_pair_gate()
    report = readable_report()
    reference = reference_report(reference_signals())
    report["tier_reference"] = {
        "version": reference["calibration_version"],
        "tier_share": reference["tier_share"],
        "tension_share": reference["tension_share"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    failures = readable_failures(report)
    if tuple(reference["ease_quantiles"]) != reading.TIER_REFERENCE:  # type: ignore[arg-type]
        failures.append("tier reference differs from reading.TIER_REFERENCE")
    if failures:
        raise SystemExit("experience gate (readable contract):\n- " + "\n- ".join(failures))
    print(
        "Radar experience audit passed: "
        f"{len(CONTEXTS)} contexts x {len(RelationshipVoice)} voices on the fixed pair; "
        f"{report['readings']} readings meet the readable contract."
    )


if __name__ == "__main__":
    audit()
