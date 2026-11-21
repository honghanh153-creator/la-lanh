"""Preset questions for "Hỏi về tháng này" (owner chose AS1 on 21.11.2026: no typed box).

People pick one of these instead of typing, so nothing they write is collected. The list comes from
what the 1000 test personas wanted to type (qa/personas/runs/month-2026-11-20/report.md): the most
common situations per topic, three per topic.

Each preset has two sentences in the copy registry, both user copy that Codex approves:
``month.preset.<id>.ask`` (the question as shown) and ``month.preset.<id>.tip`` (one plain thing to
try for that exact situation). The rest of the answer still comes from the person's chart.
"""

from __future__ import annotations

from enum import StrEnum

from app.domains.month_answer.facts import Topic


class PresetId(StrEnum):
    WORK_HARD_TALK = "work.hard_talk"
    WORK_TOO_MUCH = "work.too_much"
    WORK_SHIFTS = "work.shifts"
    MONEY_MONTH_END = "money.month_end"
    MONEY_ASK_BACK = "money.ask_back"
    MONEY_SAY_NO = "money.say_no"
    LOVE_CLOSER = "love.closer"
    LOVE_SAY_TIRED = "love.say_tired"
    LOVE_FAR = "love.far"
    FAMILY_PARENTS_ASK = "family.parents_ask"
    FAMILY_MY_PATH = "family.my_path"
    FAMILY_COMPARE = "family.compare"
    STUDY_MANY_EXAMS = "study.many_exams"
    STUDY_EXAM_ENERGY = "study.exam_energy"
    STUDY_START_PROJECT = "study.start_project"
    MIND_HOMESICK = "mind.homesick"
    MIND_SLEEP = "mind.sleep"
    MIND_HEAVY = "mind.heavy"


def preset_topic(preset: PresetId) -> Topic:
    return Topic(preset.value.split(".", 1)[0])


def presets_for(topic: Topic) -> tuple[PresetId, ...]:
    return tuple(preset for preset in PresetId if preset_topic(preset) is topic)


def ask_id(preset: PresetId) -> str:
    return f"month.preset.{preset.value}.ask"


def tip_id(preset: PresetId) -> str:
    return f"month.preset.{preset.value}.tip"


def preset_copy_ids() -> tuple[str, ...]:
    return tuple(cid for preset in PresetId for cid in (ask_id(preset), tip_id(preset)))
