"""Catalog format of the content grammar (spec: docs/foundation/la-lanh-content-grammar-spec.md §2).

A catalog is one ``catalog.json`` per surface plus one JSON file per frame. Every frame lists
its slots in template order. Values are referenced by stable ids, so constraints, combination
codes and the Roast mapping survive copy edits of the text.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SPEC_VERSION = "content-grammar-spec/v1"
DEFAULT_BUCKET = "_default"
_ID = r"^[a-z0-9][a-z0-9_-]{0,63}$"
_PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


class Surface(StrEnum):
    DAILY = "daily"
    TAROT = "tarot"
    RADAR = "radar"
    COMPANION = "companion"


class Voice(StrEnum):
    DIRECT = "direct"
    ROAST = "roast"


class SlotKind(StrEnum):
    MUST_CHANGE = "must_change"  # differs between two consecutive calendar days
    REPEATABLE = "repeatable"  # may stay the same (G0: a single value only)
    BUCKET = "bucket"  # depends on the day's bucket; outside commitment (a)


class VocabClass(StrEnum):
    HEADLINE = "headline"
    SCENE = "scene"
    ACTION = "action"
    COMPANION = "companion"
    NEUTRAL = "neutral"


class Value(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=_ID)
    text: str = Field(max_length=160)
    vocab_class: VocabClass | None = None  # defaults to the frame's class
    negative: bool = False  # carries a negative idea (role split, §3.7)
    tags: tuple[str, ...] = ()
    grammar: dict[str, str] = Field(default_factory=dict)  # word class, final particle, ...


class Slot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: SlotKind
    values: tuple[Value, ...] = ()
    by: str | None = Field(default=None, pattern=_ID)  # bucket dimension (lens, focus, ...)
    buckets: dict[str, tuple[Value, ...]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Slot:
        if self.kind is SlotKind.BUCKET:
            if self.by is None or not self.buckets or self.values:
                raise ValueError("a bucket slot needs `by` and `buckets`, and no flat values")
            if DEFAULT_BUCKET not in self.buckets:
                raise ValueError("a bucket slot needs a `_default` list")
            groups: Iterable[tuple[Value, ...]] = self.buckets.values()
        else:
            if self.by is not None or self.buckets or not self.values:
                raise ValueError("only a bucket slot takes `by`/`buckets`; others need values")
            groups = (self.values,)
        for group in groups:
            if not group:
                raise ValueError("every value list needs at least one value")
            ids = [value.id for value in group]
            if len(ids) != len(set(ids)):
                raise ValueError("value ids must be unique within a list")
        return self

    def values_for(self, bucket_key: str | None) -> tuple[Value, ...]:
        if self.kind is not SlotKind.BUCKET:
            return self.values
        return self.buckets.get(bucket_key or DEFAULT_BUCKET, self.buckets[DEFAULT_BUCKET])

    def all_values(self) -> tuple[Value, ...]:
        if self.kind is not SlotKind.BUCKET:
            return self.values
        return tuple(value for group in self.buckets.values() for value in group)


class Constraint(BaseModel):
    """``if`` every listed slot has one of the listed value ids, then ``forbid``/``require``."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    when: dict[str, tuple[str, ...]] = Field(alias="if")
    forbid: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    require: dict[str, tuple[str, ...]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_effect(self) -> Constraint:
        if not self.when or not (self.forbid or self.require):
            raise ValueError("a constraint needs `if` and `forbid` or `require`")
        return self

    def allows(self, choice: dict[str, str]) -> bool:
        if not all(choice.get(slot) in ids for slot, ids in self.when.items()):
            return True
        if any(choice.get(slot) in ids for slot, ids in self.forbid.items()):
            return False
        return all(choice.get(slot) in ids for slot, ids in self.require.items())


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Literal["authored", "ai_authoring"] = "authored"
    model: str | None = None
    prompt_version: str | None = None
    reviewed_by: str | None = None
    date: str | None = None

    @model_validator(mode="after")
    def validate_ai(self) -> Provenance:
        if self.source == "ai_authoring" and not (self.model and self.prompt_version):
            raise ValueError("AI-authored values need model and prompt_version (plan §14.3)")
        return self


class ReviewedException(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(min_length=1, max_length=64)
    slot: str | None = None
    reason: str = Field(min_length=1, max_length=300)
    reviewed_by: str = Field(min_length=1, max_length=64)


class Frame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,95}$")
    surface: Surface
    part: str = Field(pattern=r"^(headline|scene|advice|companion|contact|role:[a-z0-9_-]+)$")
    voice: Voice = Voice.DIRECT
    roast_of: str | None = None  # a roast frame names its direct frame
    template: str = Field(min_length=1, max_length=200)
    slots: dict[str, Slot]
    constraints: tuple[Constraint, ...] = ()
    meaning_key: str = Field(pattern=_ID)
    negative_role: bool = False
    vocab_class: VocabClass
    provenance: Provenance = Provenance()
    reviewed_exceptions: tuple[ReviewedException, ...] = ()

    @model_validator(mode="after")
    def validate_frame(self) -> Frame:
        if set("{}") & set(_PLACEHOLDER.sub("", self.template)):
            raise ValueError("a template may only contain plain {slot} placeholders")
        placeholders = _PLACEHOLDER.findall(self.template)
        if len(placeholders) != len(set(placeholders)) or set(placeholders) != set(self.slots):
            raise ValueError("template placeholders must name every slot exactly once")
        if list(self.slots) != placeholders:
            raise ValueError("slots must be listed in template order")
        if (self.voice is Voice.ROAST) != (self.roast_of is not None):
            raise ValueError("exactly the roast frames name `roast_of`")
        known = {
            slot: {value.id for value in slot_def.all_values()}
            for slot, slot_def in self.slots.items()
        }
        for constraint in self.constraints:
            for part in (constraint.when, constraint.forbid, constraint.require):
                for slot, ids in part.items():
                    if slot not in known or not set(ids) <= known[slot]:
                        raise ValueError(f"constraint names an unknown slot or value: {slot}")
        return self

    @property
    def must_change(self) -> tuple[str, ...]:
        return tuple(n for n, s in self.slots.items() if s.kind is SlotKind.MUST_CHANGE)

    @property
    def bucket_dims(self) -> tuple[str, ...]:
        return tuple(
            sorted({s.by for s in self.slots.values() if s.kind is SlotKind.BUCKET and s.by})
        )

    def value_class(self, value: Value) -> VocabClass:
        return value.vocab_class or self.vocab_class


class Article(BaseModel):
    """Frames shown together in one reading; they share L and the day's position p."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,95}$")
    frames: tuple[str, ...] = Field(min_length=1)


class BuildLimits(BaseModel):
    """Owner decision A4 (docs/plans/2026-10-16-p0-owner-decisions.md)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_combinations_per_bucket: int = Field(default=200_000, ge=1, le=200_000)
    max_buckets: int = Field(default=48, ge=1, le=48)
    max_search_steps: int = Field(default=2_000_000, ge=1, le=2_000_000)


class SurfaceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: Surface
    catalog_version: str = Field(pattern=r"^[a-z0-9][a-z0-9_.-]{0,63}$")
    schedule_length: int = Field(ge=2, le=10_000)  # L (owner A2: >= 90 for served frames)
    min_schedule_length: int = Field(default=90, ge=2)
    variants: int = Field(default=4, ge=1, le=8)  # M (owner A4: 4-8)
    min_variants: int = Field(default=4, ge=1, le=8)
    limits: BuildLimits = BuildLimits()
    articles: tuple[Article, ...] = ()
    serving: bool = False  # G0: nothing is served from the grammar yet
