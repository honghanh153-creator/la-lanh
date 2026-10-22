"""US-22 AC01-AC03 release gate for Hợp gu on the 50 synthetic pairs (audit 2026-10-22 R01/R06).

    uv run python -m scripts.audit_radar_us22          # report; exit 1 while a criterion fails

Every number is measured on what the web shows (``radar_sentences``), never on evidence cards:

- AC01: each reading with at least two certain contacts has >= 2 visible "fit"/"friction"
  sentences that are specific to one contact. A sentence is specific to the directed contact
  ``(body_a, aspect, body_b)`` when at least two different pairs show it and every reading that
  shows it, across the whole corpus, has that contact (replicated, so a sentence that merely
  happens to be unique to one pair is not credited). Generic aspect or planet phrases shown for
  many different contacts do not count.
  Low-signal pairs (the renderer's own condition) are reported as an honest exception.
- AC02: same pair and voice, another context changes >= 50% of the fit/friction sentences on
  average; same pair and context, another voice changes >= 50% of them on average.
- AC03: mean share of a reading's sentences also shown for another pair (same context and voice)
  is < 30%.

Not in ``pnpm check`` until the R03 content lands; ``tests/scripts/test_radar_us22_gate.py``
holds it as a strict expected failure so it turns red the moment it starts passing.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import RelationshipBundle
from app.domains.radar.reading import _motifs, build_radar_reading
from app.domains.relationships.models import RelationshipVoice
from scripts.variety_baseline import (
    RADAR_CONTEXTS,
    _radar_chart,
    changed_share,
    radar_sentences,
)

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/variety/radar-pairs-v1.json"
FIT_FRICTION = ("fit", "friction")
AC01_MIN_SPECIFIC = 2
AC02_MIN_CHANGE = 0.5
AC03_MAX_OVERLAP = 0.3

ContactKey = tuple[str, str, str]


def _contacts(bundle: RelationshipBundle) -> set[ContactKey]:
    return {(c.body_a.value, c.kind, c.body_b.value) for c in bundle.synastry.contacts}


def contact_specific(
    sentences: dict[tuple[str, str, str], list[str]], contacts: dict[str, set[ContactKey]]
) -> set[str]:
    """Sentences shown by >= 2 pairs whose every showing reading shares one directed contact."""

    shared: dict[str, set[ContactKey]] = {}
    pairs: dict[str, set[str]] = defaultdict(set)
    for (pid, _, _), shown in sentences.items():
        for sentence in set(shown):
            shared[sentence] = (
                shared[sentence] & contacts[pid] if sentence in shared else set(contacts[pid])
            )
            pairs[sentence].add(pid)
    return {sentence for sentence, common in shared.items() if common and len(pairs[sentence]) > 1}


def us22_gate(fixtures: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    engine = NatalChartEngine()
    readings: dict[tuple[str, str, str], dict[str, Any]] = {}
    contacts: dict[str, set[ContactKey]] = {}
    low_signal: set[str] = set()
    for pair in fixtures["pairs"]:
        bundle = engine.calculate_relationship_bundle(
            _radar_chart(engine, pair["a"]), _radar_chart(engine, pair["b"])
        )
        contacts[pair["id"]] = _contacts(bundle)
        if not _motifs(bundle):
            low_signal.add(pair["id"])
        for context in RADAR_CONTEXTS:
            for voice in RelationshipVoice:
                readings[(pair["id"], context, voice.value)] = build_radar_reading(
                    bundle, context=context, voice=voice
                )
    pair_ids = [pair["id"] for pair in fixtures["pairs"]]
    voices = [voice.value for voice in RelationshipVoice]
    fit_friction = {key: radar_sentences(r, FIT_FRICTION) for key, r in readings.items()}

    credited = contact_specific(fit_friction, contacts)
    specific_counts: list[int] = []
    short: list[str] = []
    for key, sentences in fit_friction.items():
        pid = key[0]
        if pid in low_signal or len(contacts[pid]) < AC01_MIN_SPECIFIC:
            continue
        count = len(set(sentences) & credited)
        specific_counts.append(count)
        if count < AC01_MIN_SPECIFIC:
            short.append("/".join(key))

    context_change = [
        changed_share(fit_friction[(pid, c1, v)], fit_friction[(pid, c2, v)])
        for pid in pair_ids
        for v in voices
        for c1, c2 in combinations(RADAR_CONTEXTS, 2)
    ]
    voice_change = [
        changed_share(fit_friction[(pid, c, v1)], fit_friction[(pid, c, v2)])
        for pid in pair_ids
        for c in RADAR_CONTEXTS
        for v1, v2 in combinations(voices, 2)
    ]
    overlap: list[float] = []
    for context in RADAR_CONTEXTS:
        for voice_key in voices:
            per_pair = {
                pid: set(radar_sentences(readings[(pid, context, voice_key)])) for pid in pair_ids
            }
            for pid, visible in per_pair.items():
                others = set().union(*(s for other, s in per_pair.items() if other != pid))
                overlap.append(len(visible & others) / len(visible) if visible else 0.0)

    report: dict[str, Any] = {
        "pairs": len(pair_ids),
        "readings": len(readings),
        "low_signal_pairs": sorted(low_signal),
        "AC01_readings_checked": len(specific_counts),
        "AC01_readings_below_two_specific": len(short),
        "AC01_specific_sentences_mean": round(statistics.fmean(specific_counts), 3)
        if specific_counts
        else 0.0,
        "AC02_context_change_mean": round(statistics.fmean(context_change), 4),
        "AC02_voice_change_mean": round(statistics.fmean(voice_change), 4),
        "AC03_cross_pair_overlap": round(statistics.fmean(overlap), 4),
    }
    failures: list[str] = []
    if short:
        failures.append(
            f"AC01: {len(short)} of {len(specific_counts)} readings have fewer than "
            f"{AC01_MIN_SPECIFIC} contact-specific fit/friction sentences (e.g. {short[:3]})"
        )
    if report["AC02_context_change_mean"] < AC02_MIN_CHANGE:
        failures.append(f"AC02 context: {report['AC02_context_change_mean']} < {AC02_MIN_CHANGE}")
    if report["AC02_voice_change_mean"] < AC02_MIN_CHANGE:
        failures.append(f"AC02 voice: {report['AC02_voice_change_mean']} < {AC02_MIN_CHANGE}")
    if report["AC03_cross_pair_overlap"] >= AC03_MAX_OVERLAP:
        failures.append(f"AC03 overlap: {report['AC03_cross_pair_overlap']} >= {AC03_MAX_OVERLAP}")
    return failures, report


def main() -> None:
    failures, report = us22_gate(json.loads(FIXTURES.read_text()))
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if failures:
        raise SystemExit("US-22 gate failed:\n- " + "\n- ".join(failures))
    print("US-22 gate passed (AC01-AC03).")


if __name__ == "__main__":
    main()
