"""Measure the variety/personalisation baseline of the CURRENT engine (P1).

Synthetic fixtures only, no network, no provider, no database. Implements the metrics of
docs/foundation/la-lanh-variety-measurement-spec.md that apply before G0/G2; the others are
reported as "not applicable yet". Writes JSON + Markdown to docs/reviews/variety-baseline-<date>/.

    uv run python -m scripts.variety_baseline            # P1 baseline (rotation off)
    uv run python -m scripts.variety_baseline --variety  # B3-1a after-report (Daily only)

``--variety`` turns on the per-person rotation with a synthetic selection key and writes
to docs/reviews/variety-a1-2026-10-17/, leaving the P1 baseline files untouched.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import unicodedata
import uuid
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, time, timedelta
from itertools import combinations, pairwise
from math import comb
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import CalculationConfig, ChartInput, NatalChart, TimePrecision
from app.domains.radar.reading import _motifs, build_radar_reading
from app.domains.readings import daily_psychology
from app.domains.readings.companion import COMPANION_FALLBACK, companion_issue_entry
from app.domains.readings.daily_psychology import DAILY_PSYCHOLOGY_MATRIX_VERSION
from app.domains.readings.daily_rotation import (
    VARIETY_KEY_VERSION,
    daily_variety_seed,
    day_index,
    derive_variety_key,
)
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    DailyTransitRole,
    DailyVariety,
    ReadingCandidate,
    ReadingPurpose,
)
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
# Synthetic selection key for the after-report; never a server secret.
SYNTHETIC_VARIETY_KEY = derive_variety_key(b"la-lanh-variety-baseline-synthetic-key")
OWNER_NAMESPACE = uuid.UUID("6f2b3c1e-6a77-4d0e-9a51-0c5f2b8d4e10")
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


NATAL_CONFIG_KINDS = frozenset({"natal_aspect", "house_placement"})


def personal_sources(transit_used: bool, support_kinds: Iterable[str]) -> int:
    """Independent personal sources actually used by one note (spec §5), each counted once.

    Source 1: a personal transit used by the note. Source 3: a natal pair aspect or a house
    placement among the evidence the situation rests on (pair + house of the same note count
    once). Single sign placements, salt and factors that exist but are unused never count.
    Sources 2 (calendar) and 4 (focus) do not exist in the current engine.
    """

    return int(transit_used) + int(bool(NATAL_CONFIG_KINDS & set(support_kinds)))


def pool_stratum(daily_pool_sizes: Sequence[int]) -> str:
    """Stratum of a profile whose eligible pool changes by day: the modal daily bucket.

    The pool is what the planner could pick from on that day (distinct issues passed to
    ``_pick``), not the issues that happened to win over the window. Ties go to the smaller
    bucket, so a small rotating pool is never reported as a large one.
    """

    order = ("1", "2-3", ">=4")
    counts = Counter(pool_bucket(size) for size in daily_pool_sizes)
    return max(order, key=lambda bucket: (counts[bucket], -order.index(bucket)))


def pool_bucket(distinct_situations: int) -> str:
    return "1" if distinct_situations <= 1 else "2-3" if distinct_situations <= 3 else ">=4"


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


# ---------------------------------------------------------------- Daily


class DailyLab:
    def __init__(self, *, variety: bool = False) -> None:
        self.variety = variety
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
        out: list[dict[str, Any]] = []
        recorded: list[int] = []
        original_pick = daily_psychology._pick
        seed = daily_variety_seed(
            SYNTHETIC_VARIETY_KEY,
            uuid.uuid5(OWNER_NAMESPACE, profile["id"]),
            DAILY_PSYCHOLOGY_MATRIX_VERSION,
        )

        def recording_pick(plan: Any, pool: list[Any]) -> Any:
            recorded.append(len({situation.issue_key for situation in pool}))
            return original_pick(plan, pool)

        daily_psychology._pick = recording_pick  # observe the pool, never change the choice
        try:
            for offset in range(DAYS):
                local_date = START + timedelta(days=offset)
                observed_at = datetime.combine(local_date, time(12), UTC)  # projection observed_at
                transits = (
                    self.engine.calculate_transit_to_natal(source, observed_at) if exact else None
                )
                recorded.clear()
                variety = (
                    DailyVariety(
                        key_version=VARIETY_KEY_VERSION,
                        catalog_version=DAILY_PSYCHOLOGY_MATRIX_VERSION,
                        seed=seed,
                        day_index=day_index(local_date),
                        # Served issues of D-1 and D-2, as the application reads them.
                        recent_issue_keys=tuple(n["issue"] for n in out[-1:-3:-1]),
                    )
                    if self.variety
                    else None
                )
                plan = self.planner.plan(
                    source,
                    purpose=ReadingPurpose.DAILY_NOTE,
                    transits=transits,
                    editorial_seed=local_date.isoformat(),
                    daily_variety=variety,
                )
                candidate = self.renderer.render(plan)
                if transits is not None and not evaluate_candidate(plan, candidate).accepted:
                    recorded.clear()
                    plan = self.planner.plan(
                        source,
                        purpose=ReadingPurpose.DAILY_NOTE,
                        editorial_seed=local_date.isoformat(),
                        daily_variety=variety,
                    )
                    candidate = self.renderer.render(plan)
                note = self._note(plan, candidate)
                # Exact plans call _pick while planning, other plans while rendering;
                # a plan that never reaches it has a pool of one.
                note["pool"] = recorded[-1] if recorded else 1
                out.append(note)
        finally:
            daily_psychology._pick = original_pick
        return out, sign

    def _note(self, plan: Any, candidate: ReadingCandidate) -> dict[str, Any]:
        self.renderer_versions.add(candidate.renderer_version)
        blueprint = candidate.semantic_blueprint
        entry = companion_issue_entry(blueprint.mechanism_key) if blueprint else None
        companion = (entry or COMPANION_FALLBACK).line.direct
        selection = plan.daily_selection
        factors = 0
        if selection is not None:
            kinds = {factor.id: str(factor.kind.value) for factor in plan.factors}
            factors = personal_sources(
                selection.transit_role is not DailyTransitRole.NONE,
                (kinds.get(ref, "") for ref in selection.support_refs),
            )
        return {
            "headline": normalize(candidate.hook),
            "scene": normalize(candidate.manifestation),
            "advice": normalize(candidate.micro_action),
            "why_today": normalize(candidate.transit) if candidate.transit else None,
            "companion": normalize(companion),
            "situation": selection.issue_key
            if selection
            else (blueprint.mechanism_key if blueprint else None),
            "issue": blueprint.mechanism_key.removeprefix("psychology:") if blueprint else "",
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
    daily_pools: Counter[str] = Counter()
    for profile in profiles:
        sizes = [n["pool"] for n in notes[profile["id"]]]
        daily_pools.update(pool_bucket(size) for size in sizes)
        time_key = "time_known" if profile["time_known"] else "date_only"
        strata[f"{time_key}|pool={pool_stratum(sizes)}|focus=none"].append(profile["id"])

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
        # Ablation keeps the salt: with rotation on, the twin is the same owner.
        twin_key = profile["birth_date"] + (f"|{profile['id']}" if lab.variety else "")
        if twin_key not in cache:
            cache[twin_key], _ = lab.notes(
                {
                    "id": profile["id"] if lab.variety else "twin",
                    "time_known": False,
                    "birth_date": profile["birth_date"],
                }
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
        "note": (
            "salt on; ablation keeps the owner's salt and changes one real signal"
            if lab.variety
            else "salt does not exist yet; ablation compares real signals only"
        ),
    }
    report: dict[str, Any] = {
        "window_days": DAYS,
        "start": START.isoformat(),
        "observed_at": "local_date 12:00 UTC (projection)",
        "voice": "direct (roast maps one-to-one onto the same baseline today)",
        "pool_rule": (
            "pool = distinct issues the planner could pick from that day (input of _pick); "
            "profile stratum = modal daily bucket, ties to the smaller bucket"
        ),
        "daily_pool_bucket_days": dict(daily_pools),
        "M1_repeat_gap_pass_rate_ge_90d": m1,
        "M2_consecutive_day_identical_rate": m2,
        "M4_identical_notes": m4,
        "M5_personal_factors": m5,
        "M7_ablation": m7,
        "M3_M6_M8": "not applicable yet (no grammar layer or chapters before G0/G2)",
        "renderer_versions": sorted(lab.renderer_versions),
    }
    if lab.variety:
        report["A1_rotation"] = rotation_report(profiles, notes)
    return report


def rotation_report(
    profiles: Sequence[dict[str, Any]], notes: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """B3-1a checks on the served notes (plan §2.3, US-21 AC02/AC05)."""

    axis_same = Counter[str]()
    same_situation_pairs = consecutive = runs_over_two = 0
    combo_repeat = {30: 0, 60: 0}
    for profile in profiles:
        series = notes[profile["id"]]
        for a, b in pairwise(series):
            consecutive += 1
            if a["issue"] == b["issue"]:
                same_situation_pairs += 1
                for part in ("headline", "scene", "advice"):
                    axis_same[part] += a[part] == b[part]
        for i in range(2, len(series)):
            window = series[i - 2 : i + 1]
            if len({n["issue"] for n in window}) == 1 and min(n["pool"] for n in window) >= 2:
                runs_over_two += 1
        for day, note in enumerate(series):
            for horizon in combo_repeat:
                if any(
                    note_key(prev) == note_key(note) for prev in series[max(0, day - horizon) : day]
                ):
                    combo_repeat[horizon] += 1
    days = sum(len(notes[p["id"]]) for p in profiles)
    return {
        "consecutive_pairs": consecutive,
        "same_situation_consecutive_pairs": same_situation_pairs,
        "same_situation_axis_repeats": dict(axis_same),
        "three_day_same_situation_runs_with_pool_ge_2": runs_over_two,
        "full_combo_seen_in_previous_30d_rate": rate(combo_repeat[30], days),
        "full_combo_seen_in_previous_60d_rate": rate(combo_repeat[60], days),
        "pool_rule": "pool = top-K (K=3) distinct issues of the day after ranking",
    }


# ---------------------------------------------------------------- Tarot

_SPREAD_FOR_COUNT = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}


def tarot_matrix(engine: TarotReadingEngine) -> list[tuple[TarotSpreadMap, TarotSpread, int]]:
    """Every spread map the engine offers, with its spread size (spec §4c: all valid maps)."""

    out = []
    for spread_map in TarotSpreadMap:
        count = len(engine.positions_for(spread_map))
        out.append((spread_map, _SPREAD_FOR_COUNT[count], count))
    return out


def duplicate_rate(values: Sequence[str]) -> float | None:
    return rate(len(values) - len(set(values)), len(values))


def different_pairs(texts_by_question: dict[str, str]) -> tuple[int, int]:
    """(pairs with different text, all pairs) among distinct questions for one card/role/topic."""

    counts = Counter(texts_by_question.values())
    n = len(texts_by_question)
    total = comb(n, 2)
    return total - sum(comb(k, 2) for k in counts.values()), total


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
    matrix = tarot_matrix(engine)
    voices = list(TarotVoice)
    headlines: dict[str, list[str]] = defaultdict(list)
    markers: Counter[str] = Counter()
    positions = readings = rejected = 0
    versions: set[str] = set()
    for item in accepted:
        rng = random.Random(f"tarot-{item['id']}")  # noqa: S311 - synthetic sampling
        for spread_map, spread, count in matrix:
            ids = tuple(card.id for card in rng.sample(cards, count))
            for voice in voices:
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
                headlines[voice.value].append(normalize(reading.headline))  # T2: per voice
                for position in reading.positions:
                    positions += 1
                    markers["meaning:Ý chính của lá"] += position.meaning_here.startswith(
                        "Ý chính của lá"
                    )
                    action = position.small_action or ""
                    markers["action:Thử nhé:"] += action.startswith("Thử nhé:")
                    markers["scene:Ví dụ:"] += position.everyday_scene.startswith("Ví dụ:")
    t2 = {
        voice: {
            "readings": len(values),
            "distinct": len(set(values)),
            "duplicate_rate": duplicate_rate(values),
        }
        for voice, values in sorted(headlines.items())
    }
    # T4: same card, same role (map position), same topic, every pair of distinct questions.
    by_topic: dict[str, list[str]] = defaultdict(list)
    for item in accepted:
        by_topic[item["context"]].append(item["question"])
    # Rotating the deck gives every (card, role) exactly once per question and map, and
    # one render records every role of that map at once.
    texts: dict[tuple[str, int, str, str], dict[str, str]] = defaultdict(dict)
    for spread_map, spread, count in matrix:
        for topic, questions in by_topic.items():
            for question in questions:
                for start_index in range(len(cards)):
                    ids = tuple(cards[(start_index + j) % len(cards)].id for j in range(count))
                    reading = engine.render(
                        card_ids=ids,
                        spread=spread,
                        spread_map=spread_map,
                        context=TarotContext(topic),
                        question=question,
                        voice=TarotVoice.PLAYFUL_GROUNDED,
                    )
                    for role_index, card_id in enumerate(ids):
                        key = (spread_map.value, role_index, topic, card_id)
                        texts[key][question] = normalize(reading.positions[role_index].meaning_here)
    t4_diff = t4_total = 0
    for by_question in texts.values():
        diff, total = different_pairs(by_question)
        t4_diff += diff
        t4_total += total
    roles = sum(count for _, _, count in matrix)
    return {
        "questions": len(accepted),
        "matrix": {
            "maps": [m.value for m, _, _ in matrix],
            "voices": [v.value for v in voices],
            "readings": readings,
            "content_rejections": rejected,
        },
        "T1_form_accuracy": "not applicable yet (the engine has no question form; US-20 adds it)",
        "T2_headline_duplicates_by_voice": t2,
        "T3_generic_markers": {"positions": positions, **dict(markers)},
        "T4_same_card_role_topic_different_text": {
            "roles": roles,
            "cards": len(cards),
            "topics": len(by_topic),
            "question_pairs": t4_total,
            "different": t4_diff,
            "rate": rate(t4_diff, t4_total),
            "voice": "playful_grounded (default)",
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


def radar_visible_texts(
    reading: dict[str, Any], sections: tuple[str, ...] | None = None
) -> list[str]:
    """Readable prose the web renders (RadarContinuePage), optionally limited to some sections.

    Top level (only for the whole reading): headline, summary, pair signature headline and
    summary, compatibility meanings. Per section: title, body, and title/body of highlights,
    scene, perspectives and observation. Labels, kickers and collapsed evidence are excluded.
    """

    texts: list[str] = []
    if sections is None:
        signature = reading.get("pair_signature") or {}
        texts += [reading.get("headline", ""), reading.get("summary", "")]
        texts += [signature.get("headline", ""), signature.get("summary", "")]
        texts += [item.get("meaning", "") for item in reading.get("compatibility_map") or []]
    for section in reading.get("sections") or []:
        if sections is not None and section.get("key") not in sections:
            continue
        texts += [section.get("title") or "", section.get("body") or ""]
        nested = [*(section.get("highlights") or []), *(section.get("perspectives") or [])]
        nested += [block for block in (section.get("scene"), section.get("observation")) if block]
        for block in nested:
            texts += [block.get("title") or "", block.get("body") or ""]
    return [text for text in texts if text]


def radar_sentences(reading: dict[str, Any], sections: tuple[str, ...] | None = None) -> list[str]:
    return [
        normalize(sentence)
        for text in radar_visible_texts(reading, sections)
        for sentence in _SENTENCE.split(text)
        if sentence.strip()
    ]


def changed_share(before: Sequence[str], after: Sequence[str]) -> float:
    base = set(before)
    return len(base - set(after)) / len(base) if base else 0.0


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
    voice_keys = [v.value for v in RelationshipVoice]
    fit_friction = ("fit", "friction")
    unique_counts: list[int] = []
    overlap_rates: list[float] = []
    for context in RADAR_CONTEXTS:
        for voice_key in voice_keys:
            per_pair = {
                pid: set(radar_sentences(readings[(pid, context, voice_key)])) for pid in pair_ids
            }
            for pid, sentences in per_pair.items():
                others: set[str] = set().union(
                    *(other_set for other, other_set in per_pair.items() if other != pid)
                )
                shared = len(sentences & others)
                unique_counts.append(len(sentences) - shared)
                overlap_rates.append(shared / len(sentences) if sentences else 0.0)
    context_change = [
        changed_share(
            radar_sentences(readings[(pid, c1, voice_key)], fit_friction),
            radar_sentences(readings[(pid, c2, voice_key)], fit_friction),
        )
        for pid in pair_ids
        for voice_key in voice_keys
        for c1, c2 in combinations(RADAR_CONTEXTS, 2)
    ]
    voice_change = [
        changed_share(
            radar_sentences(readings[(pid, context, v1)], fit_friction),
            radar_sentences(readings[(pid, context, v2)], fit_friction),
        )
        for pid in pair_ids
        for context in RADAR_CONTEXTS
        for v1, v2 in combinations(voice_keys, 2)
    ]
    voice_change_full = [
        changed_share(
            radar_sentences(readings[(pid, context, v1)]),
            radar_sentences(readings[(pid, context, v2)]),
        )
        for pid in pair_ids
        for context in RADAR_CONTEXTS
        for v1, v2 in combinations(voice_keys, 2)
    ]
    any_reading = next(iter(readings.values()))
    return {
        "pairs": len(pair_ids),
        "readings": len(readings),
        "sentence_source": (
            "visible prose per RadarContinuePage: headline, summary, pair signature, "
            "compatibility meanings; section title/body and highlights, scene, perspectives, "
            "observation title/body"
        ),
        "R1_unique_sentences_per_reading": {
            "mean": round(statistics.fmean(unique_counts), 2),
            "p10": sorted(unique_counts)[len(unique_counts) // 10],
            "note": (
                "baseline proxy: sentences not shared with any other pair "
                "(contact sentences are tagged only after R2)"
            ),
        },
        "R2_context_change_fit_friction": {
            "comparisons": len(context_change),
            "mean_changed_share": round(statistics.fmean(context_change), 4),
        },
        "R2_voice_change_fit_friction": {
            "comparisons": len(voice_change),
            "mean_changed_share": round(statistics.fmean(voice_change), 4),
        },
        "diagnostic_voice_change_full_reading": {
            "comparisons": len(voice_change_full),
            "mean_changed_share": round(statistics.fmean(voice_change_full), 4),
        },
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


def variety_markdown(report: dict[str, Any]) -> str:
    """Daily-only tables for the B3-1a after-report (Tarot and Radar are unchanged by A1)."""

    full = markdown({**report, "tarot": "unchanged by A1", "radar": "unchanged by A1"})
    head, _, _ = full.partition("\n## Tarot")
    return (
        head.replace("# Variety baseline: generated tables", "# B3-1a after-report: tables")
        + "\n## A1 rotation\n\n```json\n"
        + json.dumps(report["daily"]["A1_rotation"], ensure_ascii=False, indent=1)
        + "\n```\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variety", action="store_true")
    args = parser.parse_args()
    profiles = json.loads((FIXTURES / "profiles-v1.json").read_text())
    pairs = json.loads((FIXTURES / "radar-pairs-v1.json").read_text())
    if args.variety:
        after: dict[str, Any] = {
            "generated_for": "B3-1a after-report (rotation on, synthetic key and data only)",
            "fixtures": {"profiles": profiles["meta"]},
            "daily": daily_report(DailyLab(variety=True), profiles),
        }
        out = ROOT / "docs" / "reviews" / "variety-a1-2026-10-17"
        out.mkdir(parents=True, exist_ok=True)
        (out / "after.json").write_text(json.dumps(after, ensure_ascii=False, indent=1) + "\n")
        (out / "after-tables.md").write_text(variety_markdown(after))
        print(json.dumps(after["daily"]["A1_rotation"], ensure_ascii=False))
        return
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
