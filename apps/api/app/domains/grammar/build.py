"""Build a surface's grammar: allowlists, master schedules and manifest (spec §3).

The build refuses (``GrammarBuildError``) instead of weakening a commitment: infeasible
schedule, vocabulary or role violation, missing Roast mapping, limit overrun or a banned
phrase left in an allowlist all turn CI red.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.domains.grammar.composer import (
    COMPOSER_VERSION,
    CombinationLimitExceeded,
    FrameAllowlist,
    buckets_of,
    build_allowlist,
    dedupe_key,
    parse_code,
)
from app.domains.grammar.gate import GATE_VERSION, sentence_failures
from app.domains.grammar.models import (
    SPEC_VERSION,
    Frame,
    SlotKind,
    SurfaceCatalog,
    VocabClass,
    Voice,
)
from app.domains.grammar.schedule import (
    Master,
    build_schedule,
    canonical_cycle,
    schedule_violations,
)

BUILD_DIR = "build"
CATALOG_FILE = "catalog.json"
FRAMES_DIR = "frames"
OUTPUT_FILES = ("allowlist.json", "schedules.json", "manifest.json")


class GrammarBuildError(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True)
class GrammarBuild:
    catalog: SurfaceCatalog
    frames: dict[str, Frame]
    outputs: dict[str, str]  # file name -> canonical JSON text


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def digest(text: str) -> str:
    return sha256(text.encode()).hexdigest()


def catalog_sha256(directory: Path) -> str:
    parts = [
        CATALOG_FILE,
        *sorted(f"{FRAMES_DIR}/{p.name}" for p in (directory / FRAMES_DIR).glob("*.json")),
    ]
    hasher = sha256()
    for relative in parts:
        hasher.update(relative.encode() + b"\x00" + (directory / relative).read_bytes() + b"\x00")
    return hasher.hexdigest()


def load_catalog(directory: Path) -> tuple[SurfaceCatalog, dict[str, Frame]]:
    reasons: list[str] = []
    try:
        catalog = SurfaceCatalog.model_validate_json((directory / CATALOG_FILE).read_text())
    except (OSError, ValidationError) as error:
        raise GrammarBuildError([f"catalog.json: {error}"]) from error
    frames: dict[str, Frame] = {}
    for path in sorted((directory / FRAMES_DIR).glob("*.json")):
        try:
            frame = Frame.model_validate_json(path.read_text())
        except ValidationError as error:
            reasons.append(f"{path.name}: {error}")
            continue
        if frame.frame_id in frames:
            reasons.append(f"{path.name}: duplicate frame_id {frame.frame_id}")
        frames[frame.frame_id] = frame
    if reasons:
        raise GrammarBuildError(reasons)
    return catalog, frames


def _structure_reasons(catalog: SurfaceCatalog, frames: dict[str, Frame]) -> list[str]:
    reasons: list[str] = []
    if catalog.schedule_length < catalog.min_schedule_length:
        reasons.append(f"L={catalog.schedule_length} < minimum {catalog.min_schedule_length}")
    if catalog.variants < catalog.min_variants:
        reasons.append(f"M={catalog.variants} < minimum {catalog.min_variants}")
    roasts: dict[str, list[str]] = {}
    for frame in frames.values():
        if frame.surface is not catalog.surface:
            reasons.append(f"{frame.frame_id}: surface {frame.surface} != {catalog.surface}")
        for name, slot in frame.slots.items():
            if slot.kind is SlotKind.REPEATABLE and len(slot.values) > 1:
                reasons.append(
                    f"{frame.frame_id}.{name}: a repeatable slot takes one value in G0 "
                    "(split the frame or make it a bucket slot)"
                )
        if len(buckets_of(frame)) > catalog.limits.max_buckets:
            reasons.append(f"{frame.frame_id}: more than {catalog.limits.max_buckets} buckets")
        if frame.roast_of is not None:
            roasts.setdefault(frame.roast_of, []).append(frame.frame_id)
            direct = frames.get(frame.roast_of)
            if direct is None or direct.voice is not Voice.DIRECT:
                reasons.append(f"{frame.frame_id}: roast_of names no direct frame")
            elif _shape(direct) != _shape(frame):
                reasons.append(
                    f"{frame.frame_id}: slots and value ids must mirror {direct.frame_id}"
                )
    for frame in frames.values():
        if frame.voice is Voice.DIRECT and len(roasts.get(frame.frame_id, [])) != 1:
            reasons.append(f"{frame.frame_id}: needs exactly one Roast frame (missing mapping)")
    return reasons


def _shape(frame: Frame) -> dict[str, Any]:
    return {
        name: (
            slot.kind.value,
            slot.by,
            sorted(v.id for v in slot.values),
            {key: sorted(v.id for v in group) for key, group in slot.buckets.items()},
        )
        for name, slot in frame.slots.items()
    }


def _article_reasons(
    catalog: SurfaceCatalog, frames: dict[str, Frame], allowlists: dict[str, FrameAllowlist]
) -> list[str]:
    """Vocabulary split and negative-role budget across the frames of one reading (§3 step 7)."""

    reasons: list[str] = []
    for article in catalog.articles:
        members = [frames[f] for f in article.frames if f in frames]
        missing = set(article.frames) - set(frames)
        if missing:
            reasons.append(f"{article.article_id}: unknown frames {sorted(missing)}")
        family = members + [
            roast for roast in frames.values() if roast.roast_of in set(article.frames)
        ]
        for voice in Voice:
            group = [frame for frame in family if frame.voice is voice]
            if sum(frame.negative_role for frame in group) > 1:
                reasons.append(f"{article.article_id}/{voice}: more than one negative_role frame")
            action_terms = {
                dedupe_key(value.text)
                for frame in group
                for slot in frame.slots.values()
                for value in slot.all_values()
                if frame.value_class(value) is VocabClass.ACTION and value.text.strip()
            }
            for frame in group:
                for slot in frame.slots.values():
                    for value in slot.all_values():
                        if value.negative and not frame.negative_role:
                            reasons.append(
                                f"{frame.frame_id}: negative value {value.id} outside the "
                                "negative_role frame"
                            )
                if frame.part not in {"headline", "scene"}:
                    continue
                for slot in frame.slots.values():
                    for value in slot.all_values():
                        if frame.value_class(value) is VocabClass.ACTION:
                            reasons.append(f"{frame.frame_id}: action value {value.id}")
                for texts in allowlists[frame.frame_id].entries.values():
                    for text in texts.values():
                        folded = dedupe_key(text)
                        leaked = sorted(
                            term
                            for term in action_terms
                            if re.search(rf"(?<!\w){re.escape(term.rstrip('.,'))}(?!\w)", folded)
                        )
                        if leaked:
                            reasons.append(
                                f"{frame.frame_id}: action vocabulary {leaked[:3]} in a "
                                f"{frame.part} sentence"
                            )
                            break
    return reasons


def build_surface(directory: Path) -> GrammarBuild:
    catalog, frames = load_catalog(directory)
    reasons = _structure_reasons(catalog, frames)
    if reasons:
        raise GrammarBuildError(reasons)

    allowlists: dict[str, FrameAllowlist] = {}
    seen: dict[Voice, dict[str, str]] = {voice: {} for voice in Voice}
    for frame_id in sorted(frames, key=lambda f: (frames[f].voice is Voice.ROAST, f)):
        frame = frames[frame_id]
        try:
            allowlists[frame_id] = build_allowlist(
                frame, catalog.limits.max_combinations_per_bucket, seen[frame.voice]
            )
        except CombinationLimitExceeded as error:
            reasons.append(str(error))
    if reasons:
        raise GrammarBuildError(reasons)

    for frame_id, allowlist in allowlists.items():
        for texts in allowlist.entries.values():
            leftovers = [t for t in texts.values() if sentence_failures(frames[frame_id], t)]
            if leftovers:
                reasons.append(f"{frame_id}: {len(leftovers)} gated sentences left in allowlist")

    schedules: dict[str, list[list[str]]] = {}
    frame_meta: dict[str, Any] = {}
    for frame_id, frame in sorted(frames.items()):
        allowlist = allowlists[frame_id]
        meta: dict[str, Any] = {
            "voice": frame.voice.value,
            "part": frame.part,
            "roast_of": frame.roast_of,
            "buckets": sorted(allowlist.entries),
            "enumerated": allowlist.enumerated,
            "constraint_dropped": allowlist.constraint_dropped,
            "gate_dropped": dict(sorted(allowlist.gate_dropped.items())),
            "duplicate_dropped": allowlist.duplicate_dropped,
            "allowlisted": sum(len(t) for t in allowlist.entries.values()),
            "allowlist_sha256": digest(canonical_json(allowlist.entries)),
        }
        frame_meta[frame_id] = meta
        if frame.voice is Voice.ROAST:
            direct_entries = allowlists[frame.roast_of or ""].entries
            missing = sum(
                1
                for bucket, codes in direct_entries.items()
                for code in codes
                if code not in allowlist.entries.get(bucket, {})
            )
            if missing:
                reasons.append(f"{frame_id}: {missing} direct combinations lack a Roast mapping")
            continue
        eligible = set.intersection(
            *(allowlist.masters(frame, bucket) for bucket in allowlist.entries)
        )
        masters = {tuple(parse_code(m)[s] for s in frame.must_change) for m in eligible}
        required = [
            {value.id for value in frame.slots[slot].all_values()} for slot in frame.must_change
        ]
        meta["masters_eligible"] = len(masters)
        for index, values in enumerate(required):
            unused = values - {master[index] for master in masters}
            if unused:
                reasons.append(
                    f"{frame_id}: {frame.must_change[index]} values {sorted(unused)} have no "
                    "combination allowed in every bucket"
                )
        variants: list[tuple[Master, ...]] = []
        variant_meta: list[dict[str, Any]] = []
        seen_cycles: set[tuple[Master, ...]] = set()
        for attempt in range(catalog.variants * 4):
            if len(variants) == catalog.variants:
                break
            result = build_schedule(
                masters,
                length=catalog.schedule_length,
                required_values=required,
                frame_id=frame_id,
                variant=attempt,
                max_steps=catalog.limits.max_search_steps,
            )
            if result.order is None:
                continue
            cycle = canonical_cycle(result.order)
            if cycle in seen_cycles:
                continue
            problems = schedule_violations(result.order, required_values=required, allowed=masters)
            if problems:  # pragma: no cover - the search only returns valid cycles
                reasons.append(f"{frame_id}: invalid schedule {problems[:3]}")
                continue
            seen_cycles.add(cycle)
            variants.append(result.order)
            codes = [
                "|".join(f"{s}={v}" for s, v in zip(frame.must_change, m, strict=True))
                for m in result.order
            ]
            variant_meta.append({"sha256": digest(canonical_json(codes)), "steps": result.steps})
        if len(variants) < catalog.min_variants:
            reasons.append(
                f"{frame_id}: built {len(variants)} schedule variants with L="
                f"{catalog.schedule_length}, need {catalog.min_variants} (infeasible)"
            )
        schedules[frame_id] = [
            ["|".join(f"{s}={v}" for s, v in zip(frame.must_change, m, strict=True)) for m in order]
            for order in variants
        ]
        meta["variants"] = variant_meta
    reasons += _article_reasons(catalog, frames, allowlists)
    if reasons:
        raise GrammarBuildError(reasons)

    allowlist_text = canonical_json({f: a.entries for f, a in sorted(allowlists.items())})
    schedules_text = canonical_json(schedules)
    manifest = {
        "spec_version": SPEC_VERSION,
        "surface": catalog.surface.value,
        "catalog_version": catalog.catalog_version,
        "catalog_sha256": catalog_sha256(directory),
        "composer_version": COMPOSER_VERSION,
        "gate_version": GATE_VERSION,
        "serving": catalog.serving,
        "L": catalog.schedule_length,
        "M": catalog.variants,
        "limits": catalog.limits.model_dump(),
        "articles": [a.model_dump() for a in catalog.articles],
        "frames": frame_meta,
        "reviewed_exceptions": {
            f: [e.model_dump() for e in frame.reviewed_exceptions]
            for f, frame in sorted(frames.items())
            if frame.reviewed_exceptions
        },
        "files": {
            "allowlist.json": digest(allowlist_text),
            "schedules.json": digest(schedules_text),
        },
    }
    return GrammarBuild(
        catalog=catalog,
        frames=frames,
        outputs={
            "allowlist.json": allowlist_text,
            "schedules.json": schedules_text,
            "manifest.json": canonical_json(manifest),
        },
    )
