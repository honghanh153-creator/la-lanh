"""Measure the variety/personalisation baseline of the CURRENT engine (P1).

Synthetic fixtures only, no network, no provider, no database. Implements the metrics of
docs/foundation/la-lanh-variety-measurement-spec.md that apply before G0/G2; the others are
reported as "not applicable yet". Writes JSON + Markdown to docs/reviews/variety-baseline-<date>/.

    uv run python -m scripts.variety_baseline
"""

from __future__ import annotations

import json
import random
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, time, timedelta
from itertools import combinations
from math import comb
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, NatalChart, TimePrecision
from app.domains.radar.reading import _motifs, build_radar_reading
from app.domains.readings.companion import COMPANION_FALLBACK, companion_issue_entry
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import DailyTransitRole, ReadingCandidate, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.relationships.models import RelationshipVoice
from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import TarotContext, TarotSpread, TarotSpreadMap, TarotVoice

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "variety"
BANK = ROOT / "docs" / "fixtures" / "tarot-question-bank-v1.json"
START = date(2026, 10, 1)
DAYS = 200
HORIZON = 90
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
PARTS = ("headline", "scene", "advice", "why_today", "companion")
RADAR_CONTEXTS = ("crush", "friend", "partner", "someone")
_SENTENCE = re.compile(r"(?<=[.!?…])\s+")
_TRAILING = re.compile(r"[\s.!?…,;:]+$")


def normalize(text: str) -> str:
    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return _TRAILING.sub("", folded)


def min_repeat_gap(sentences: Sequence[str | None]) -> int | None:
    """Shortest distance in days between two occurrences of the same sentence (None: no repeat)."""

    last: dict[str, int] = {}
    best: int | None = None
    for day, sentence in enumerate(sentences):
        if sentence is None:
            continue
        if sentence in last:
            gap = day - last[sentence]
            best = gap if best is None else min(best, gap)
        last[sentence] = day
    return best


def identical_pair_rate(groups: Iterable[Counter[str]]) -> tuple[int, int]:
    """(identical pairs, all pairs) over groups of note keys, e.g. one group per sign and day."""

    same = total = 0
    for counts in groups:
        n = sum(counts.values())
        total += comb(n, 2)
        same += sum(comb(k, 2) for k in counts.values())
    return same, total


def note_key(note: dict[str, Any]) -> tuple[str, str, str]:
    return (note["headline"], note["scene"], note["advice"])


def pool_bucket(distinct_situations: int) -> str:
    return "1" if distinct_situations <= 1 else "2-3" if distinct_situations <= 3 else ">=4"


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


# ---------------------------------------------------------------- Daily


class DailyLab:
    def __init__(self) -> None:
        self.engine = NatalChartEngine()
        self.planner = ReadingPlanner()
        self.renderer = DeterministicVietnameseRenderer()
        self.config = CalculationConfig.western_recommended()
        self.renderer_versions: set[str] = set()

    def chart(self, profile: dict[str, Any]) -> NatalChart:
        hour, minute = (int(x) for x in profile["birth_time_local"].split(":"))
        local = datetime.combine(date.fromisoformat(profile["birth_date"]), time(hour, minute), TZ)
        return self.engine.calculate_chart(
            ChartInput(
                utc_datetime=local.astimezone(UTC),
                latitude=profile["latitude"],
                longitude=profile["longitude"],
            ),
            self.config,
        )

    def notes(self, profile: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
        exact = profile["time_known"]
        source: Any = (
            self.chart(profile)
            if exact
            else self.engine.calculate_date_only_sun(date.fromisoformat(profile["birth_date"]))
        )
        if exact:
            sun = next(b for b in source.bodies if b.body.value == "sun")
            sign = sun.sign.value
        else:
            sign = (
                source.sign.value if source.sign else "|".join(c.value for c in source.candidates)
            )
        out = []
        for offset in range(DAYS):
            local_date = START + timedelta(days=offset)
            observed_at = datetime.combine(local_date, time(12), UTC)  # projection observed_at
            transits = (
                self.engine.calculate_transit_to_natal(source, observed_at) if exact else None
            )
            plan = self.planner.plan(
                source,
                purpose=ReadingPurpose.DAILY_NOTE,
                transits=transits,
                editorial_seed=local_date.isoformat(),
            )
            candidate = self.renderer.render(plan)
            if transits is not None and not evaluate_candidate(plan, candidate).accepted:
                plan = self.planner.plan(
                    source, purpose=ReadingPurpose.DAILY_NOTE, editorial_seed=local_date.isoformat()
                )
                candidate = self.renderer.render(plan)
            out.append(self._note(plan, candidate))
        return out, sign

    def _note(self, plan: Any, candidate: ReadingCandidate) -> dict[str, Any]:
        self.renderer_versions.add(candidate.renderer_version)
        blueprint = candidate.semantic_blueprint
        entry = companion_issue_entry(blueprint.mechanism_key) if blueprint else None
        companion = (entry or COMPANION_FALLBACK).line.direct
        selection = plan.daily_selection
        factors = 0
        if selection is not None:
            if selection.transit_role is not DailyTransitRole.NONE:
                factors += 1  # source 1: a certain personal transit
            elif selection.rule_key.startswith("pair-") or "house" in selection.rule_key:
                factors += 1  # source 3: a natal pair or house rule
        return {
            "headline": normalize(candidate.hook),
            "scene": normalize(candidate.manifestation),
            "advice": normalize(candidate.micro_action),
            "why_today": normalize(candidate.transit) if candidate.transit else None,
            "companion": normalize(companion),
            "situation": selection.issue_key
            if selection
            else (blueprint.mechanism_key if blueprint else None),
            "factors": factors,
        }


def daily_report(lab: DailyLab, fixtures: dict[str, Any]) -> dict[str, Any]:
    profiles = fixtures["profiles"]
    notes: dict[str, list[dict[str, Any]]] = {}
    signs: dict[str, str] = {}
    for profile in profiles:
        notes[profile["id"]], signs[profile["id"]] = lab.notes(profile)
    strata: dict[str, list[str]] = {
        f"{t}|pool={pool}|focus=none": []
        for t in ("time_known", "date_only")
        for pool in ("1", "2-3", ">=4")
    }
    for profile in profiles:
        situations = {n["situation"] for n in notes[profile["id"]]}
        time_key = "time_known" if profile["time_known"] else "date_only"
        strata[f"{time_key}|pool={pool_bucket(len(situations))}|focus=none"].append(profile["id"])

    m1: dict[str, Any] = {}
    m2: dict[str, Any] = {}
    m5: dict[str, Any] = {}
    for stratum, ids in sorted(strata.items()):
        row: dict[str, Any] = {
            "profiles": len(ids),
            "sample": "ok" if len(ids) >= 50 else "insufficient",
        }
        repeat_row: dict[str, Any] = {}
        if not ids:
            m1[stratum], m2[stratum], m5[stratum] = row, {}, {}
            continue
        for part in PARTS:
            if all(n[part] is None for i in ids for n in notes[i]):
                row[part] = "not applicable (part never shown in this stratum)"
                repeat_row[part] = None
                continue
            gaps = [min_repeat_gap([n[part] for n in notes[i]]) for i in ids]
            passed = sum(1 for g in gaps if g is None or g >= HORIZON)
            observed = [g for g in gaps if g is not None]
            row[part] = {
                "pass_rate": rate(passed, len(ids)),
                "median_min_gap_days": statistics.median(observed) if observed else None,
                "never_repeats": len(gaps) - len(observed),
            }
            same = sum(
                1
                for i in ids
                for a, b in zip(notes[i], notes[i][1:], strict=False)
                if a[part] is not None and a[part] == b[part]
            )
            pairs = sum(
                1
                for i in ids
                for a, b in zip(notes[i], notes[i][1:], strict=False)
                if a[part] is not None
            )
            repeat_row[part] = rate(same, pairs)
        m1[stratum] = row
        m2[stratum] = repeat_row
        counts = [n["factors"] for i in ids for n in notes[i]]
        m5[stratum] = {
            "mean": round(statistics.fmean(counts), 3),
            "p10": sorted(counts)[len(counts) // 10],
            "distribution": dict(Counter(counts)),
        }

    m4: dict[str, Any] = {}
    for time_known in (True, False):
        groups: list[Counter[str]] = []
        for day in range(DAYS):
            by_sign: dict[str, Counter[str]] = defaultdict(Counter)
            for profile in profiles:
                if profile["time_known"] is time_known:
                    by_sign[signs[profile["id"]]][
                        json.dumps(note_key(notes[profile["id"]][day]))
                    ] += 1
            groups.extend(by_sign.values())
        same, total = identical_pair_rate(groups)
        m4["time_known" if time_known else "date_only"] = {
            "identical_pairs": same,
            "pairs": total,
            "rate": rate(same, total),
        }
    pair_same = pair_days = 0
    for first, second in fixtures["same_birthdate_pairs"]:
        first_notes, _ = lab.notes(first)
        second_notes, _ = lab.notes(second)
        pair_same += sum(
            1 for x, y in zip(first_notes, second_notes, strict=True) if note_key(x) == note_key(y)
        )
        pair_days += DAYS
    m4["same_birthdate_date_only_pairs"] = {
        "identical_days": pair_same,
        "days": pair_days,
        "rate": rate(pair_same, pair_days),
    }

    changed = total = 0
    cache: dict[str, list[dict[str, Any]]] = {}
    for profile in profiles:
        if not profile["time_known"]:
            continue
        twin_key = profile["birth_date"]
        if twin_key not in cache:
            cache[twin_key], _ = lab.notes(
                {"id": "twin", "time_known": False, "birth_date": twin_key}
            )
        for x, y in zip(notes[profile["id"]], cache[twin_key], strict=True):
            changed += note_key(x) != note_key(y)
            total += 1
    day_changed = sum(
        1
        for profile in profiles
        for prev, nxt in zip(notes[profile["id"]], notes[profile["id"]][1:], strict=False)
        if note_key(prev) != note_key(nxt)
    )
    day_pairs = sum(DAYS - 1 for _ in profiles)
    m7 = {
        "remove_birth_time_changes_note": rate(changed, total),
        "next_day_changes_note": rate(day_changed, day_pairs),
        "note": "salt does not exist yet; ablation compares real signals only",
    }
    return {
        "window_days": DAYS,
        "start": START.isoformat(),
        "observed_at": "local_date 12:00 UTC (projection)",
        "voice": "direct (roast maps one-to-one onto the same baseline today)",
        "M1_repeat_gap_pass_rate_ge_90d": m1,
        "M2_consecutive_day_identical_rate": m2,
        "M4_identical_notes": m4,
        "M5_personal_factors": m5,
        "M7_ablation": m7,
        "M3_M6_M8": "not applicable yet (no grammar layer or chapters before G0/G2)",
        "renderer_versions": sorted(lab.renderer_versions),
    }


# ---------------------------------------------------------------- Tarot


def tarot_report() -> dict[str, Any]:
    engine = TarotReadingEngine()
    cards = all_cards()
    bank = json.loads(BANK.read_text())
    accepted = [
        item
        for item in bank["items"]
        if item["expected"]["accepted"]
        and item.get("form") != "timing"
        and item["context"]
        and engine.assess_question(item["question"], TarotContext(item["context"])).accepted
    ]
    spreads = (
        (TarotSpread.ONE_CARD, TarotSpreadMap.ONE_FOCUS, 1),
        (TarotSpread.THREE_CARD, TarotSpreadMap.THREE_UNBLOCK, 3),
    )
    headlines: dict[str, list[str]] = defaultdict(list)
    markers: Counter[str] = Counter()
    readings = 0
    rejected = 0
    versions: set[str] = set()
    for item in accepted:
        rng = random.Random(f"tarot-{item['id']}")  # noqa: S311 - synthetic sampling, not security
        for spread, spread_map, count in spreads:
            ids = tuple(card.id for card in rng.sample(cards, count))
            for voice in (TarotVoice.PLAYFUL_GROUNDED, TarotVoice.ROAST):
                try:
                    reading = engine.render(
                        card_ids=ids,
                        spread=spread,
                        spread_map=spread_map,
                        context=TarotContext(item["context"]),
                        question=item["question"],
                        voice=voice,
                    )
                except TarotContentRejected:
                    rejected += 1
                    continue
                readings += 1
                versions.add(reading.provenance.knowledge_version)
                headlines[f"{voice.value}|{spread_map.value}"].append(normalize(reading.headline))
                for position in reading.positions:
                    markers["meaning:Ý chính của lá"] += position.meaning_here.startswith(
                        "Ý chính của lá"
                    )
                    markers["action:Thử nhé:"] += position.small_action.startswith("Thử nhé:")
                    markers["scene:Ví dụ:"] += position.everyday_scene.startswith("Ví dụ:")
    t2 = {
        key: {
            "readings": len(values),
            "distinct": len(set(values)),
            "duplicate_rate": rate(len(values) - len(set(values)), len(values)),
        }
        for key, values in sorted(headlines.items())
    }
    # T4: same card in the same role, different questions of the same topic.
    t4_same = t4_pairs = 0
    by_context: dict[str, list[str]] = defaultdict(list)
    for item in accepted:
        by_context[item["context"]].append(item["question"])
    for context, questions in by_context.items():
        sample = questions[:10]
        for card in cards:
            texts = []
            for question in sample:
                reading = engine.render(
                    card_ids=(card.id,),
                    spread=TarotSpread.ONE_CARD,
                    spread_map=TarotSpreadMap.ONE_FOCUS,
                    context=TarotContext(context),
                    question=question,
                    voice=TarotVoice.PLAYFUL_GROUNDED,
                )
                texts.append(normalize(reading.positions[0].meaning_here))
            for a, b in combinations(texts, 2):
                t4_pairs += 1
                t4_same += a == b
    return {
        "questions": len(accepted),
        "readings": readings,
        "content_rejections": rejected,
        "T1_form_accuracy": "not applicable yet (the engine has no question form; US-20 adds it)",
        "T2_headline_duplicates": t2,
        "T3_generic_markers_positions": dict(markers),
        "T4_same_card_role_different_text": {
            "pairs": t4_pairs,
            "different": t4_pairs - t4_same,
            "rate": rate(t4_pairs - t4_same, t4_pairs),
        },
        "knowledge_versions": sorted(versions),
    }


# ---------------------------------------------------------------- Radar


def _radar_chart(engine: NatalChartEngine, person: dict[str, Any]) -> NatalChart:
    known = person["time_known"]
    clock = person["birth_time_local"] if known else "12:00"
    hour, minute = (int(x) for x in clock.split(":"))
    local = datetime.combine(date.fromisoformat(person["birth_date"]), time(hour, minute), TZ)
    chart = engine.calculate_chart(
        ChartInput(
            utc_datetime=local.astimezone(UTC),
            latitude=person["latitude"],
            longitude=person["longitude"],
        ),
        CalculationConfig.western_recommended(),
    )
    if known:
        return chart
    # Same treatment as BirthService.calculate_transient_chart for an unknown time.
    return chart.model_copy(
        update={
            "time_precision": TimePrecision.UNKNOWN,
            "bodies": tuple(b for b in chart.bodies if b.body.value != "moon"),
            "aspects": tuple(
                a for a in chart.aspects if "moon" not in {a.body_a.value, a.body_b.value}
            ),
            "houses": None,
            "angles": None,
        }
    )


def _radar_sentences(reading: dict[str, Any], sections: tuple[str, ...] | None = None) -> list[str]:
    texts: list[str] = []
    if sections is None:
        texts += [reading["headline"], reading["summary"]]
    for section in reading["sections"]:
        if sections is not None and section.get("key") not in sections:
            continue
        texts += [section.get("title") or "", section.get("body") or ""]
        texts += [h.get("body", "") for h in section.get("highlights", [])]
    return [normalize(s) for t in texts for s in _SENTENCE.split(t) if s.strip()]


def radar_report(fixtures: dict[str, Any]) -> dict[str, Any]:
    engine = NatalChartEngine()
    readings: dict[tuple[str, str, str], dict[str, Any]] = {}
    low_signal = 0
    for pair in fixtures["pairs"]:
        bundle = engine.calculate_relationship_bundle(
            _radar_chart(engine, pair["a"]), _radar_chart(engine, pair["b"])
        )
        low_signal += not _motifs(bundle)  # the renderer's own low-signal condition
        for context in RADAR_CONTEXTS:
            for voice in RelationshipVoice:
                readings[(pair["id"], context, voice.value)] = build_radar_reading(
                    bundle, context=context, voice=voice
                )
    pair_ids = [p["id"] for p in fixtures["pairs"]]
    unique_counts: list[int] = []
    overlap_rates: list[float] = []
    for context in RADAR_CONTEXTS:
        for voice in RelationshipVoice:
            per_pair = {
                pid: set(_radar_sentences(readings[(pid, context, voice.value)]))
                for pid in pair_ids
            }
            for pid, sentences in per_pair.items():
                others = set().union(*(s for other, s in per_pair.items() if other != pid))
                shared = len(sentences & others)
                unique_counts.append(len(sentences) - shared)
                overlap_rates.append(shared / len(sentences) if sentences else 0.0)
    fit_friction = ("fit", "friction")

    def changed_share(a: list[str], b: list[str]) -> float:
        base = set(a)
        return len(base - set(b)) / len(base) if base else 0.0

    context_change = [
        changed_share(
            _radar_sentences(
                readings[(pid, c1, RelationshipVoice.STRAIGHT_WARM.value)], fit_friction
            ),
            _radar_sentences(
                readings[(pid, c2, RelationshipVoice.STRAIGHT_WARM.value)], fit_friction
            ),
        )
        for pid in pair_ids
        for c1, c2 in combinations(RADAR_CONTEXTS, 2)
    ]
    voice_change = [
        changed_share(
            _radar_sentences(readings[(pid, "crush", v1.value)]),
            _radar_sentences(readings[(pid, "crush", v2.value)]),
        )
        for pid in pair_ids
        for v1, v2 in combinations(list(RelationshipVoice), 2)
    ]
    any_reading = next(iter(readings.values()))
    return {
        "pairs": len(pair_ids),
        "readings": len(readings),
        "R1_unique_sentences_per_reading": {
            "mean": round(statistics.fmean(unique_counts), 2),
            "p10": sorted(unique_counts)[len(unique_counts) // 10],
            "note": (
                "baseline proxy: sentences not shared with any other pair "
                "(contact sentences are tagged only after R2)"
            ),
        },
        "R2_context_change_fit_friction": round(statistics.fmean(context_change), 4),
        "R2_voice_change_all_sections": round(statistics.fmean(voice_change), 4),
        "R3_cross_pair_overlap": round(statistics.fmean(overlap_rates), 4),
        "low_signal_pairs": low_signal,
        "unknown_time_method": (
            "partner at local noon, Moon/houses/angles removed (current BirthService behaviour)"
        ),
        "versions": {
            k: any_reading["metadata"].get(k)
            for k in ("knowledge_version", "renderer_version", "gate_version")
        },
    }


# ---------------------------------------------------------------- Report


def markdown(report: dict[str, Any]) -> str:
    """Tables generated from baseline.json (the narrative report is written separately)."""

    d = report["daily"]
    lines = [
        "# Variety baseline: generated tables",
        "",
        f"Fixtures: {json.dumps(report['fixtures'], ensure_ascii=False)}",
        "",
    ]
    lines += [
        "## Daily M1 (pass rate: shortest repeat gap >= 90 days)"
        " and M2 (identical to the previous day)",
        "",
    ]
    lines += [
        "| Stratum | Profiles | " + " | ".join(PARTS) + " |",
        "|---|---|" + "---|" * len(PARTS),
    ]
    for stratum, row in d["M1_repeat_gap_pass_rate_ge_90d"].items():
        cells = []
        for part in PARTS:
            value = row.get(part)
            if isinstance(value, dict):
                m2 = d["M2_consecutive_day_identical_rate"][stratum].get(part)
                cells.append(f"{value['pass_rate']} (gap {value['median_min_gap_days']}; M2 {m2})")
            else:
                cells.append("n/a" if value else "—")
        lines.append(
            f"| {stratum} | {row['profiles']} ({row['sample']}) | " + " | ".join(cells) + " |"
        )
    lines += [
        "",
        "## Daily M4 / M5 / M7",
        "",
        f"- M4: {json.dumps(d['M4_identical_notes'], ensure_ascii=False)}",
    ]
    lines += [
        f"- M5: {json.dumps(d['M5_personal_factors'], ensure_ascii=False)}",
        f"- M7: {json.dumps(d['M7_ablation'], ensure_ascii=False)}",
    ]
    lines += [
        "",
        "## Tarot",
        "",
        "```json",
        json.dumps(report["tarot"], ensure_ascii=False, indent=1),
        "```",
    ]
    lines += [
        "",
        "## Radar",
        "",
        "```json",
        json.dumps(report["radar"], ensure_ascii=False, indent=1),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    profiles = json.loads((FIXTURES / "profiles-v1.json").read_text())
    pairs = json.loads((FIXTURES / "radar-pairs-v1.json").read_text())
    report = {
        "generated_for": "P1 variety baseline (current engine, synthetic data only)",
        "fixtures": {
            "profiles": profiles["meta"],
            "radar_pairs": pairs["meta"],
            "tarot_bank": json.loads(BANK.read_text())["version"],
        },
        "daily": daily_report(DailyLab(), profiles),
        "tarot": tarot_report(),
        "radar": radar_report(pairs),
    }
    out = ROOT / "docs" / "reviews" / "variety-baseline-2026-10-16"
    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    (out / "baseline-tables.md").write_text(markdown(report))
    print(
        json.dumps({k: report[k] for k in ("daily", "tarot", "radar")}, ensure_ascii=False)[:4000]
    )


if __name__ == "__main__":
    main()
