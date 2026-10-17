"""Enumerate, compose, normalise, gate and de-duplicate every combination (spec §3 steps 1-5)."""

from __future__ import annotations

import itertools
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from app.domains.grammar.gate import sentence_failures
from app.domains.grammar.models import DEFAULT_BUCKET, Frame, SlotKind, Value

COMPOSER_VERSION = "grammar-composer-v1"
NO_BUCKET = "_all"
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.!?;:…])")


class CombinationLimitExceeded(ValueError):
    pass


def normalize(text: str) -> str:
    """NFC, single spaces, no space before punctuation, capital first letter (spec §3 step 2)."""

    text = " ".join(unicodedata.normalize("NFC", text).split())
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    return text[:1].upper() + text[1:]


def dedupe_key(text: str) -> str:
    return normalize(text).casefold()


def code_of(frame: Frame, choice: dict[str, str], slots: tuple[str, ...] | None = None) -> str:
    return "|".join(f"{slot}={choice[slot]}" for slot in (slots or tuple(frame.slots)))


def master_of(frame: Frame, choice: dict[str, str]) -> str:
    return code_of(frame, choice, frame.must_change)


def parse_code(code: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in code.split("|"))


def buckets_of(frame: Frame) -> dict[str, dict[str, str]]:
    """Every bucket of a frame: the product of the keys of each bucket dimension."""

    dims = frame.bucket_dims
    if not dims:
        return {NO_BUCKET: {}}
    keys_per_dim = [
        sorted(
            {
                key
                for slot in frame.slots.values()
                if slot.kind is SlotKind.BUCKET and slot.by == dim
                for key in slot.buckets
            }
        )
        for dim in dims
    ]
    out: dict[str, dict[str, str]] = {}
    for keys in itertools.product(*keys_per_dim):
        bucket = dict(zip(dims, keys, strict=True))
        out[bucket_id(bucket)] = bucket
    return out


def bucket_id(bucket: dict[str, str]) -> str:
    return ",".join(f"{dim}={key}" for dim, key in sorted(bucket.items())) or NO_BUCKET


def resolve_bucket(frame: Frame, context: dict[str, str]) -> str:
    """The bucket of a runtime context; unknown or missing keys fall back to ``_default``."""

    bucket = {}
    for dim in frame.bucket_dims:
        keys = {
            key
            for slot in frame.slots.values()
            if slot.kind is SlotKind.BUCKET and slot.by == dim
            for key in slot.buckets
        }
        key = context.get(dim, DEFAULT_BUCKET)
        bucket[dim] = key if key in keys else DEFAULT_BUCKET
    return bucket_id(bucket)


@dataclass
class FrameAllowlist:
    frame_id: str
    entries: dict[str, dict[str, str]] = field(default_factory=dict)  # bucket -> code -> text
    enumerated: int = 0
    constraint_dropped: int = 0
    gate_dropped: Counter[str] = field(default_factory=Counter)
    duplicate_dropped: int = 0

    def masters(self, frame: Frame, bucket: str) -> set[str]:
        return {master_of(frame, parse_code(code)) for code in self.entries.get(bucket, {})}


def _choices(frame: Frame, bucket: dict[str, str]) -> tuple[list[str], list[tuple[Value, ...]]]:
    names = list(frame.slots)
    groups = [
        frame.slots[name].values_for(bucket.get(frame.slots[name].by or "")) for name in names
    ]
    return names, groups


def compose(frame: Frame, values: dict[str, Value]) -> str:
    return normalize(frame.template.format(**{slot: value.text for slot, value in values.items()}))


def build_allowlist(
    frame: Frame, max_combinations: int, seen_texts: dict[str, str]
) -> FrameAllowlist:
    """Allowlist of one frame. ``seen_texts`` (text -> frame_id) de-duplicates across frames."""

    result = FrameAllowlist(frame_id=frame.frame_id)
    owner_of_text: dict[str, str] = {}  # dedupe key -> master code within this frame
    for bid, bucket in sorted(buckets_of(frame).items()):
        names, groups = _choices(frame, bucket)
        total = 1
        for group in groups:
            total *= len(group)
        if total > max_combinations:
            raise CombinationLimitExceeded(
                f"{frame.frame_id} [{bid}]: {total} combinations > {max_combinations}"
            )
        entries: dict[str, str] = {}
        bucket_texts: set[str] = set()
        for combo in itertools.product(*groups):
            result.enumerated += 1
            values = dict(zip(names, combo, strict=True))
            choice = {slot: value.id for slot, value in values.items()}
            if not all(constraint.allows(choice) for constraint in frame.constraints):
                result.constraint_dropped += 1
                continue
            text = compose(frame, values)
            failures = sentence_failures(frame, text)
            if failures:
                result.gate_dropped.update(failures)
                continue
            key, master = dedupe_key(text), master_of(frame, choice)
            # One sentence belongs to one master combination (so commitment (b) holds across
            # buckets), appears once per bucket, and belongs to one frame per surface/voice.
            if (
                owner_of_text.get(key, master) != master
                or key in bucket_texts
                or seen_texts.get(key, frame.frame_id) != frame.frame_id
            ):
                result.duplicate_dropped += 1
                continue
            owner_of_text[key] = master
            bucket_texts.add(key)
            entries[code_of(frame, choice)] = text
        result.entries[bid] = entries
    for key in owner_of_text:
        seen_texts.setdefault(key, frame.frame_id)
    return result
