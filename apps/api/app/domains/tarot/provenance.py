"""Provenance for the framed Tarot Luna payload (US-20 AC06, B2-4b).

Spec: docs/plans/2026-10-18-b2-4b-tarot-provenance-task.md.

Every string the provider could receive is either a closed label or catalog text with a code:

* ``position_source`` finds, for one rendered position, the catalog codes whose resolution
  equals what the reader sees (role frame + lead, scene, reflection, action). Nothing is parsed
  out of the question; when no code reproduces the text, there is no source and no request.
* ``resolve_position`` and ``resolve_summary`` rebuild the text from those codes alone. The
  reducer builds the payload from these resolutions, not from the reading's strings.
* ``untraced_paths`` walks every string in a payload and returns the paths it cannot trace to a
  closed label or a catalog code. The compiler refuses any payload with an untraced path, and
  tests run it over the whole question bank.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from app.domains.tarot import action_copy, question_frame, roles, stance
from app.domains.tarot.engine import (
    _POSITIONS,
    TarotReadingEngine,
    _CardMeaning,
    _resource_step,
    _shown_step,
    _tension_parts,
    card_scene,
    step_clause,
)
from app.domains.tarot.knowledge import card_by_id
from app.domains.tarot.meaning_brief import (
    BRIEF_LIMITS,
    GOAL_KEYS,
    goal_action,
    goal_by_key,
    links_for,
    question_goals,
)
from app.domains.tarot.models import (
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotQuestionIntent,
    TarotReading,
    TarotSpreadMap,
    TarotStanceKind,
    TarotStanceLevel,
    TarotVoice,
)

PROVENANCE_VERSION = "tarot-provenance-v1"
MEANING_BRIEF_V3 = "tarot-meaning-brief-v3"
_ROLE_CODE = re.compile(r"^(?P<key>[a-z_]{2,20})\.(?P<index>[0-2])$")
_LEAD_CODE = re.compile(r"^(?P<form>[a-z_]{2,10})\.(?P<index>[0-4])$")
_GOAL_CODE = re.compile(r"^goal\.(?P<key>[a-z_]{2,20})$")
# T02/T03: the asked action's scene or step, with the frame topic it was chosen for.
_ACTION_CODE = re.compile(r"^act\.(?P<action>[a-z_]{2,20})\.(?P<topic>[a-z_]{2,20})$")
_ACTION_CODES = tuple(f"act.{a.value}.{t.value}" for a in TarotAction for t in TarotContext)
# Codex r47: the preparation step of an action, or the step of an unsettled choice.
_PREP_CODES = tuple(f"prep.{key}" for key in action_copy.PREP_STEPS)


def _action_code(code: str) -> tuple[TarotAction, TarotContext]:
    match = _ACTION_CODE.fullmatch(code)
    if match is None:
        raise ValueError("unknown action copy code")
    return TarotAction(match["action"]), TarotContext(match["topic"])


def _has_step(code: str, position_key: str) -> bool:
    asked, topic = _action_code(code)
    return action_copy.action_step(asked, position_key, topic) is not None


def _fields(card_id: str, topic: TarotContext) -> tuple[str, str, str]:
    meaning = _CardMeaning.for_context(card_by_id(card_id), topic)
    return meaning.core, _tension_parts(meaning.tension)[0], _resource_step(meaning.resource)


def _lead_codes() -> Iterator[str | None]:
    yield None
    for form, leads in roles.LEADS.items():
        for index in range(len(leads)):
            yield f"{form.value}.{index}"


def _lead_text(code: str | None) -> str | None:
    if code is None:
        return None
    match = _LEAD_CODE.fullmatch(code)
    if match is None:
        raise ValueError("unknown lead code")
    return roles.LEADS[TarotQuestionForm(match["form"])][int(match["index"])]


def resolve_meaning(
    frame: str, lead: str | None, gentle: bool, *, position_key: str, card_id: str, topic: Any
) -> str:
    match = _ROLE_CODE.fullmatch(frame)
    if match is None or match["key"] != position_key:
        raise ValueError("role frame code does not belong to this position")
    core, tension, resource = _fields(card_id, TarotContext(topic))
    text = roles.meaning_for(
        position_key,
        core=core,
        tension=tension,
        resource=resource,
        frame=int(match["index"]),
        lead=_lead_text(lead),
    )
    return f"{text} {roles.GENTLE_CHECK}" if gentle else text


def resolve_reflection(
    code: str, *, position_key: str, topic: TarotContext, intent: TarotQuestionIntent
) -> str:
    if code == "role":
        return TarotReadingEngine._reflection(position_key, topic, intent)
    match = _GOAL_CODE.fullmatch(code)
    if match is None or match["key"] not in GOAL_KEYS:
        raise ValueError("unknown reflection code")
    return goal_by_key(match["key"]).reflection


def resolve_scene(code: str | None, *, card_id: str, topic: TarotContext) -> str:
    """The card x topic scene (no code), or the asked action's scene (``act.<action>.<topic>``)."""

    if code is None:
        return roles.scene_without_label(card_scene(card_id, topic))
    scene = action_copy.action_scene(*_action_code(code))
    if scene is None:
        raise ValueError("action has no scene")
    return roles.scene_without_label(scene)


def resolve_action(code: str | None, *, position_key: str, card_id: str, topic: Any) -> str | None:
    if code is None:
        return None
    if code == "card":
        return roles.action_for(_CardMeaning.for_context(card_by_id(card_id), topic).resource)
    if code.startswith("prep."):
        return action_copy.PREP_STEPS[code.removeprefix("prep.")]
    if code.startswith("act."):
        asked, asked_topic = _action_code(code)
        step = action_copy.action_step(asked, position_key, asked_topic)
        if step is None:
            raise ValueError("action has no step for this position")
        return step
    match = _GOAL_CODE.fullmatch(code)
    if match is None or match["key"] not in GOAL_KEYS:
        raise ValueError("unknown action code")
    action = goal_action(goal_by_key(match["key"]), position_key)
    if action is None:
        raise ValueError("goal has no action for this position")
    return action


def resolve_position(
    source: Mapping[str, Any],
    *,
    position_key: str,
    card_id: str,
    topic: TarotContext,
    intent: TarotQuestionIntent,
) -> dict[str, str | None]:
    """The four authored texts of a position, rebuilt from its codes only.

    ``lead`` and ``action`` are optional in the privacy schema (default null) and the minimiser
    drops null keys, so an absent key means null, exactly as the schema reads it."""

    return {
        "meaning_here": resolve_meaning(
            source["frame"],
            source.get("lead"),
            bool(source["gentle"]),
            position_key=position_key,
            card_id=card_id,
            topic=topic,
        ),
        "everyday_scene": resolve_scene(source.get("scene"), card_id=card_id, topic=topic),
        "reflection_question": resolve_reflection(
            source["reflection"], position_key=position_key, topic=topic, intent=intent
        ),
        "small_action": resolve_action(
            source.get("action"), position_key=position_key, card_id=card_id, topic=topic
        ),
    }


def position_source(
    reading: TarotReading, index: int, goal_keys: Sequence[str]
) -> dict[str, Any] | None:
    """Catalog codes that reproduce the rendered position exactly, or None when none do.

    Roast readings are never sent to a provider, so only the direct register is searched.
    """

    position = reading.positions[index]
    key, card_id, topic = position.key, position.card.id, reading.context
    gentle = reading.voice is TarotVoice.GENTLE_SPECIFIC
    frame = next(
        (
            (code, lead)
            for code in (roles.frame_code(key, i) for i in range(roles.FRAME_VARIANTS))
            for lead in _lead_codes()
            if resolve_meaning(code, lead, gentle, position_key=key, card_id=card_id, topic=topic)
            == position.meaning_here
        ),
        None,
    )
    reflection = next(
        (
            code
            for code in ("role", *(f"goal.{k}" for k in goal_keys))
            if resolve_reflection(
                code, position_key=key, topic=topic, intent=reading.question_intent
            )
            == position.reflection_question
        ),
        None,
    )
    action_codes: list[str | None] = [None]
    scene_codes: list[str | None] = [None]
    if key in roles.STEP_ROLES:
        # Closed labels only: every action x topic code is tried, nothing is read from the text.
        action_codes = [
            *(c for c in _ACTION_CODES if _has_step(c, key)),
            *_PREP_CODES,
            *(f"goal.{k}" for k in goal_keys if goal_action(goal_by_key(k), key) is not None),
            "card",
        ]
        scene_codes = [
            *(c for c in _ACTION_CODES if action_copy.action_scene(*_action_code(c))),
            None,
        ]
    scene = next(
        (
            (code,)
            for code in scene_codes
            if resolve_scene(code, card_id=card_id, topic=topic) == position.everyday_scene
        ),
        None,
    )
    if scene is not None and scene[0] is not None and _has_step(scene[0], key):
        # Most steps read the same for every topic: name the step by the scene's topic.
        action_codes = [scene[0], *(c for c in action_codes if c != scene[0])]
    action = next(
        (
            (code,)
            for code in action_codes
            if resolve_action(code, position_key=key, card_id=card_id, topic=topic)
            == position.small_action
        ),
        None,
    )
    if frame is None or reflection is None or action is None or scene is None:
        return None
    return {
        "frame": frame[0],
        "lead": frame[1],
        "gentle": gentle,
        "reflection": reflection,
        "action": action[0],
        "scene": scene[0],
    }


def _views(
    spread_map: TarotSpreadMap, card_ids: Sequence[str], topic: TarotContext
) -> list[stance.PositionView]:
    views = []
    for (key, label), card_id in zip(_POSITIONS[spread_map], card_ids, strict=True):
        core, tension, resource = _fields(card_id, topic)
        views.append(
            stance.PositionView(
                key=key,
                label=label,
                card_id=card_id,
                title=card_by_id(card_id).title_vi,
                core=core,
                tension=tension,
                resource=resource,
            )
        )
    return views


def resolve_summary(
    *,
    spread_map: TarotSpreadMap,
    card_ids: Sequence[str],
    topic: TarotContext,
    goal_keys: Sequence[str],
    readiness: bool,
    step: str | None,
) -> str:
    """The plain summary, rebuilt from cards, goal codes, the readiness flag and the step
    position's action (itself resolved from its codes)."""

    lead = tuple(goal_by_key(k).meaning for k in goal_keys if k != "general")
    reserve = len(question_frame.READINESS_NOTE.split()) if readiness else 0
    summary = stance.plain_summary(_views(spread_map, card_ids, topic), step, lead, reserve)
    return f"{question_frame.READINESS_NOTE} {summary}" if readiness else summary


def _resolved_step(
    positions: Sequence[Mapping[str, Any]],
    keys: Sequence[str],
    topic: TarotContext,
    intent: TarotQuestionIntent,
) -> str | None:
    """The step the summary ends on, from the step position's codes only (never its text)."""

    for position, key in zip(positions, keys, strict=False):
        if key not in roles.STEP_ROLES:
            continue
        source = position.get("source")
        if not isinstance(source, Mapping):
            return None
        action = resolve_position(
            source,
            position_key=key,
            card_id=card_by_id(position.get("card_key", "")).id,
            topic=topic,
            intent=intent,
        )["small_action"]
        return step_clause(action)
    return None


def stance_labels(reading: TarotReading) -> dict[str, Any] | None:
    current = reading.stance
    if current is None:
        return None
    return {
        "kind": current.kind.value,
        "level": current.level.value,
        "action": current.action.value if current.action else None,
        "options": [option.value for option in current.options] if current.options else None,
    }


def goal_keys_for(reading: TarotReading) -> tuple[str, ...]:
    """Closed goal codes classified locally (as the renderer did); never matched text.

    Frame v2 readings classified goals from the asked text, older ones from the whole question
    (T01). The reading does not say which, and nothing about the frame is exposed, so both
    classifications are tried and only one that reproduces the stored summary is used; with
    neither, the brief fails closed (no request)."""

    readiness = reading.summary.startswith(f"{question_frame.READINESS_NOTE} ")
    candidates: list[tuple[str, ...]] = []
    for text in (question_frame.asked_text(reading.question), reading.question):
        keys = tuple(goal.key for goal in question_goals(text, reading.context))
        if keys not in candidates:
            candidates.append(keys)
    for keys in candidates:
        summary = resolve_summary(
            spread_map=reading.spread_map,
            card_ids=[position.card.id for position in reading.positions],
            topic=reading.context,
            goal_keys=keys,
            readiness=readiness,
            step=_shown_step(reading.positions),
        )
        if summary == reading.summary:
            return keys
    return candidates[0]


def framed_brief(reading: TarotReading) -> dict[str, Any] | None:
    """Meaning brief v3 for a framed reading, built from catalog codes; None if the reading's
    summary is not reproduced by them (then nothing is sent)."""

    goal_keys = goal_keys_for(reading)
    readiness = reading.summary.startswith(f"{question_frame.READINESS_NOTE} ")
    card_ids = [position.card.id for position in reading.positions]
    summary = resolve_summary(
        spread_map=reading.spread_map,
        card_ids=card_ids,
        topic=reading.context,
        goal_keys=goal_keys,
        readiness=readiness,
        step=_shown_step(reading.positions),
    )
    if summary != reading.summary:
        return None
    keys = [position.key for position in reading.positions]
    return {
        "version": MEANING_BRIEF_V3,
        "topic": reading.context.value,
        "intent": reading.question_intent.value,
        "spread_map": reading.spread_map.value,
        "goals": [{"key": key, "meaning": goal_by_key(key).meaning} for key in goal_keys],
        "local_summary": summary,
        "summary_source": {"readiness": readiness},
        "links": links_for(set(zip(card_ids, keys, strict=True)), reading.context),
        "limits": list(BRIEF_LIMITS),
        "stance": stance_labels(reading),
    }


def framed_positions(reading: TarotReading) -> list[dict[str, Any]] | None:
    """Provider positions for a framed reading: every text resolved from its codes."""

    goal_keys = goal_keys_for(reading)
    labels = dict(_POSITIONS[reading.spread_map])
    positions: list[dict[str, Any]] = []
    for index, position in enumerate(reading.positions):
        source = position_source(reading, index, goal_keys)
        if source is None:
            return None
        card = card_by_id(position.card.id)
        resolved = resolve_position(
            source,
            position_key=position.key,
            card_id=card.id,
            topic=reading.context,
            intent=reading.question_intent,
        )
        positions.append(
            {
                "position_key": position.key,
                "position_label": labels[position.key],
                "card_key": card.id,
                "card_title": card.title_vi,
                "orientation": "upright",
                "meaning_keys": list(card.source_concept_ids),
                **resolved,
                "source": source,
            }
        )
    return positions


# ---------------------------------------------------------------- tracing


def _strings(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _strings(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            yield from _strings(item, f"{path}[{index}]")


def untraced_paths(
    payload: Mapping[str, Any],
    *,
    focus_sentences: Mapping[str, str],
    limits: frozenset[str],
) -> list[str]:
    """Paths of strings in a framed (brief v3) payload that trace to no label or catalog code.

    ``focus_sentences`` and ``limits`` are the privacy module's closed tables (passed in so this
    domain module does not import the provider layer).
    """

    traced: set[str] = set()
    values = dict(_strings(payload))

    def label(path: str, allowed: Any) -> None:
        if path in values and values[path] in allowed:
            traced.add(path)

    def text(path: str, expected: str | None) -> None:
        if path in values and expected is not None and values[path] == expected:
            traced.add(path)

    try:
        brief = payload["meaning_brief"]
        topic = TarotContext(brief["topic"])
        intent = TarotQuestionIntent(brief["intent"])
        spread_map = TarotSpreadMap(brief["spread_map"])
        positions = payload["positions"]
        keys = [key for key, _ in _POSITIONS[spread_map]]
        labels = dict(_POSITIONS[spread_map])
        card_ids = [position["card_key"] for position in positions]
        goal_keys = [goal["key"] for goal in brief["goals"]]
    except (KeyError, TypeError, ValueError):
        return sorted(values)

    label("category", {"relationship", "work", "self", "general"})
    label("focus_key", set(focus_sentences))
    text("focus_sentence", focus_sentences.get(values.get("focus_key", "")))
    label("meaning_brief.version", {"tarot-meaning-brief-v3"})
    label("meaning_brief.topic", {c.value for c in TarotContext})
    label("meaning_brief.intent", {i.value for i in TarotQuestionIntent})
    label("meaning_brief.spread_map", {m.value for m in TarotSpreadMap})
    for index, goal in enumerate(brief["goals"]):
        base = f"meaning_brief.goals[{index}]"
        label(f"{base}.key", GOAL_KEYS)
        if goal.get("key") in GOAL_KEYS:
            text(f"{base}.meaning", goal_by_key(goal["key"]).meaning)
    for index in range(len(brief.get("limits", ()))):
        label(f"meaning_brief.limits[{index}]", limits)
    stance_value = brief.get("stance")
    if isinstance(stance_value, Mapping):
        label("meaning_brief.stance.kind", {k.value for k in TarotStanceKind})
        label("meaning_brief.stance.level", {lv.value for lv in TarotStanceLevel})
        label("meaning_brief.stance.action", {a.value for a in TarotAction})
        for index in range(len(stance_value.get("options") or ())):
            label(f"meaning_brief.stance.options[{index}]", {a.value for a in TarotAction})
    if len(card_ids) == len(keys):
        summary_source = brief.get("summary_source") or {}
        try:
            expected_summary = resolve_summary(
                spread_map=spread_map,
                card_ids=card_ids,
                topic=topic,
                goal_keys=goal_keys,
                readiness=bool(summary_source.get("readiness")),
                step=_resolved_step(positions, keys, topic, intent),
            )
        except (KeyError, StopIteration, ValueError):
            expected_summary = None
        text("meaning_brief.local_summary", expected_summary)
        # Links are recomputed from the positions; a supplied link must be one of them.
        rebuilt = {
            link["key"]: link for link in links_for(set(zip(card_ids, keys, strict=True)), topic)
        }
        for index, link in enumerate(brief.get("links", ())):
            base = f"meaning_brief.links[{index}]"
            known = rebuilt.get(link.get("key"))
            if known is None:
                continue
            label(f"{base}.key", {known["key"]})
            label(f"{base}.kind", {known["kind"]})
            text(f"{base}.meaning", str(known["meaning"]))
            for inner in range(len(link.get("source_positions", ()))):
                label(f"{base}.source_positions[{inner}]", set(keys))
    for index, position in enumerate(positions):
        base = f"positions[{index}]"
        if index >= len(keys) or position.get("position_key") != keys[index]:
            continue
        key, card_id = keys[index], position.get("card_key", "")
        try:
            card = card_by_id(card_id)
        except KeyError:
            continue
        label(f"{base}.position_key", {key})
        text(f"{base}.position_label", labels[key])
        label(f"{base}.card_key", {card.id})
        text(f"{base}.card_title", card.title_vi)
        label(f"{base}.orientation", {"upright"})
        for inner in range(len(position.get("meaning_keys", ()))):
            label(f"{base}.meaning_keys[{inner}]", set(card.source_concept_ids))
        source = position.get("source")
        if not isinstance(source, Mapping):
            continue
        try:
            resolved = resolve_position(
                source, position_key=key, card_id=card.id, topic=topic, intent=intent
            )
        except (KeyError, StopIteration, ValueError):
            continue
        for field, expected in resolved.items():
            text(f"{base}.{field}", expected)
        label(f"{base}.source.frame", {source.get("frame")} - {None})
        if source.get("lead") is not None:
            label(f"{base}.source.lead", {source.get("lead")})
        label(f"{base}.source.reflection", {source.get("reflection")} - {None})
        if source.get("action") is not None:
            label(f"{base}.source.action", {source.get("action")})
        if source.get("scene") is not None:
            label(f"{base}.source.scene", {source.get("scene")})
    return sorted(set(values) - traced)
