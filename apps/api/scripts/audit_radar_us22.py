"""US-22 AC01-AC03 release gate for Hợp gu on the 50 synthetic pairs (audit 2026-10-22 R01/R06).

    uv run python -m scripts.audit_radar_us22          # report; exit 1 while a criterion fails

Every number is measured on what the web shows (``radar_sentences``), never on evidence cards:

- AC01: each reading with at least two certain contacts has >= 2 visible "fit"/"friction"
  sentences that are specific to one directed contact ``(body_a, aspect, body_b)``. Credit needs
  two independent things (Codex #47):
  1. a **closed source catalog** that binds the text to exactly that directed contact and to no
     other (``contact_source_catalog()``: ``app.domains.radar.contact_copy.CONTACT_LINES``, built
     from the owner-approved R03 copy; absent today, so nothing can be credited);
  2. provenance the reading declares (``highlights[].contact_lines: [{text, evidence_id}]``), which
     the audit checks: the evidence id is a real contact of this pair in this direction and is
     cited by that highlight; the text is visible; corpus-wide it is never declared for another
     contact and never shown in a reading without that contact.
  The renderer's own declarations never certify text by themselves; generic, planet-only,
  aspect-only or scene text cannot qualify. Low-signal pairs are an honest exception.
- AC02: same pair and voice, another context changes >= 50% of the fit/friction sentences on
  average; same pair and context, another voice changes >= 50% of them on average.
- AC03: mean share of a reading's sentences also shown for another pair (same context and voice)
  is < 30%.

Not in ``pnpm check`` until the R03 content lands; ``tests/scripts/test_radar_us22_gate.py``
holds it as a strict expected failure so it turns red the moment it starts passing.
"""

from __future__ import annotations

import importlib
import json
import statistics
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
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
    normalize,
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


def _evidence_key(evidence_id: str) -> ContactKey | None:
    """``syn:mars:trine:venus:0.40`` -> ``("mars", "trine", "venus")``; other sources -> None."""

    parts = evidence_id.split(":")
    return (parts[1], parts[2], parts[3]) if len(parts) >= 4 and parts[0] == "syn" else None


DeclaredLine = tuple[str, ContactKey | None, frozenset[ContactKey | None]]


def declared_lines(reading: dict[str, Any]) -> list[DeclaredLine]:
    """``(normalised text, declared contact, contacts cited by the same highlight)``."""

    lines: list[DeclaredLine] = []
    for section in reading.get("sections", []):
        if section.get("key") not in FIT_FRICTION:
            continue
        for item in section.get("highlights") or []:
            cited = frozenset(_evidence_key(e) for e in item.get("evidence_ids", []))
            for line in item.get("contact_lines") or []:
                lines.append((normalize(line["text"]), _evidence_key(line["evidence_id"]), cited))
    return lines


def contact_source_catalog() -> Mapping[ContactKey, Collection[str]]:
    """The closed text -> directed-contact source, independent of what the renderer declares.

    It is the approved R03 contact copy once wired (``app.domains.radar.contact_copy``); until then
    it is empty and no sentence can earn AC01 credit.
    """

    try:
        module = importlib.import_module("app.domains.radar.contact_copy")
    except ModuleNotFoundError:
        return {}
    lines: Mapping[ContactKey, Collection[str]] = getattr(module, "CONTACT_LINES", {})
    return lines


def contact_specific(
    visible: dict[tuple[str, str, str], list[str]],
    contacts: dict[str, set[ContactKey]],
    declared: Mapping[tuple[str, str, str], Sequence[DeclaredLine]],
    catalog: Mapping[ContactKey, Collection[str]] | None = None,
) -> dict[tuple[str, str, str], set[str]]:
    """Per reading, the visible sentences credited to one directed contact (see AC01 above)."""

    source = contact_source_catalog() if catalog is None else catalog
    bound: dict[str, set[ContactKey]] = defaultdict(set)
    for source_contact, texts in source.items():
        for source_text in texts:
            bound[normalize(source_text)].add(source_contact)

    claimed: dict[str, set[ContactKey | None]] = defaultdict(set)
    for lines in declared.values():
        for text, contact, _ in lines:
            claimed[text].add(contact)
    shown_by: dict[str, set[str]] = defaultdict(set)
    for (pid, _, _), sentences in visible.items():
        for sentence in sentences:
            shown_by[sentence].add(pid)
    credited: dict[tuple[str, str, str], set[str]] = {}
    for key, sentences in visible.items():
        pid, shown = key[0], set(sentences)
        credited[key] = {
            text
            for text, contact, cited in declared.get(key, [])
            if contact is not None
            and bound.get(text) == {contact}
            and text in shown
            and contact in cited
            and contact in contacts[pid]
            and claimed[text] == {contact}
            and all(contact in contacts[other] for other in shown_by[text])
        }
    return credited


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
    declared = {key: declared_lines(r) for key, r in readings.items()}

    credited = contact_specific(fit_friction, contacts, declared)
    specific_counts: list[int] = []
    short: list[str] = []
    for key in fit_friction:
        pid = key[0]
        if pid in low_signal or len(contacts[pid]) < AC01_MIN_SPECIFIC:
            continue
        count = len(credited[key])
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
