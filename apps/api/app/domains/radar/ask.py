""" "Hỏi về hai bạn" (Hợp gu direction B, owner AL1 20.11.2026).

Pre-written questions by relationship group and topic, answered from the facts already in the
pair's stored reading: the level of each theme in the "Vì sao" layer. No free text, no external
AI, no new data: an answer is a pure function of (question, stored reading).

Rules (radar spec §8, panel 20.11):
- Answers talk about the two people together ("hai bạn"), never what the absent person thinks,
  feels or wants; the panel flagged a draft line ("người ấy dễ nghe câu rõ ý") as judging, so
  "Vì sao" lines describe the pair only.
- A question that asks for the other person's mind gets the fixed refusal with a sentence the
  user can send instead.
- Every line lives in the copy registry (``radar.ask.*``); a question is offered only when all
  lines it can show are approved, so nothing unapproved ever reaches a user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.content.copy_approval import approved_copy
from app.domains.radar.reading import LEVEL_LABELS, THEME_PLAIN

ASK_VERSION = "radar-ask-v1"
PREFIX = "radar.ask."

# Relationship group of each reading context; "someone" (results before AL1) reads as friends.
GROUPS = {
    "crush": "close",
    "partner": "close",
    "friend": "friend",
    "someone": "friend",
    "coworker": "work",
    "family": "family",
}

# Topic → the themes it is answered from, in order of relevance.
TOPICS = {
    "message": ("communication", "clarity"),
    "timing": ("pace", "freedom"),
    "together": ("attraction", "pace", "visibility"),
    "direct": ("intensity", "communication", "emotional", "clarity"),
}
MIND = "mind"  # asks for the other person's mind: always the refusal
QUESTIONS = (*TOPICS, MIND)

# Stored theme levels → answer level. "quiet" (a theme not in the reading) reads as balanced
# with its own "Vì sao" line.
ANSWER_LEVELS = {"good": "good", "balanced": "balanced", "watch": "watch"}
ANSWER_PARTS = ("say", "why", "try")


@dataclass(frozen=True)
class Answer:
    question_id: str
    question: str
    say: str
    why: str
    try_today: str | None
    can_send: str
    refusal: bool
    based_on: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": ASK_VERSION,
            "question_id": self.question_id,
            "question": self.question,
            "say": self.say,
            "why": self.why,
            "try_today": self.try_today,
            "can_send": self.can_send,
            "refusal": self.refusal,
            "based_on": self.based_on,
        }


def registry_ids() -> list[str]:
    """Every registry id this module can read (for coverage tests)."""

    ids: list[str] = []
    for group in sorted(set(GROUPS.values())):
        ids += [f"{PREFIX}{group}.{question}.question" for question in QUESTIONS]
        ids += [f"{PREFIX}{group}.{topic}.send" for topic in TOPICS]
        ids.append(f"{PREFIX}{group}.{MIND}.send")
    for topic in TOPICS:
        for level in ANSWER_LEVELS.values():
            ids += [f"{PREFIX}{topic}.{level}.{part}" for part in ANSWER_PARTS]
    ids += [f"{PREFIX}why.quiet", f"{PREFIX}{MIND}.reply"]
    return ids


def _ids_for(group: str, question: str) -> list[str]:
    ids = [f"{PREFIX}{group}.{question}.question", f"{PREFIX}{group}.{question}.send"]
    if question == MIND:
        return [*ids, f"{PREFIX}{MIND}.reply"]
    ids.append(f"{PREFIX}why.quiet")
    for level in ANSWER_LEVELS.values():
        ids += [f"{PREFIX}{question}.{level}.{part}" for part in ANSWER_PARTS]
    return ids


def _ready(group: str, question: str) -> bool:
    return all(approved_copy(entry_id) is not None for entry_id in _ids_for(group, question))


def _text(entry_id: str) -> str:
    text = approved_copy(entry_id)
    if text is None:  # pragma: no cover - guarded by _ready
        raise LookupError(entry_id)
    return text


def questions_for(reading: dict[str, Any]) -> list[dict[str, str]]:
    """The questions this reading can answer now: approved lines only, refusal last."""

    group = GROUPS.get(str(reading.get("context") or "someone"), "friend")
    return [
        {"id": question, "text": _text(f"{PREFIX}{group}.{question}.question")}
        for question in QUESTIONS
        if _ready(group, question)
    ]


def _factors(reading: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Theme key → factor from the reading's "Vì sao" layer (readable-v2 results)."""

    for section in reading.get("sections") or []:
        if section.get("key") == "why":
            return {
                str(factor["key"]): factor
                for factor in section.get("factors") or []
                if isinstance(factor, dict) and "key" in factor
            }
    return {}


def answer(reading: dict[str, Any], question_id: str) -> Answer:
    """Answer ``question_id`` from the stored reading. Raises KeyError for an unknown or
    not yet approved question."""

    group = GROUPS.get(str(reading.get("context") or "someone"), "friend")
    if question_id not in QUESTIONS or not _ready(group, question_id):
        raise KeyError(question_id)
    question = _text(f"{PREFIX}{group}.{question_id}.question")
    send = _text(f"{PREFIX}{group}.{question_id}.send")
    if question_id == MIND:
        return Answer(
            question_id=question_id,
            question=question,
            say=_text(f"{PREFIX}{MIND}.reply"),
            why="",
            try_today=None,
            can_send=send,
            refusal=True,
            based_on=None,
        )
    factors = _factors(reading)
    # The most telling theme for this topic: one to watch first, then a good one, then any.
    present = [factors[theme] for theme in TOPICS[question_id] if theme in factors]
    lead = next(
        (factor for level in ("watch", "good", "balanced") for factor in present
         if factor.get("level") == level),
        None,
    )  # fmt: skip
    level = ANSWER_LEVELS.get(str(lead.get("level")), "balanced") if lead else "balanced"
    base = f"{PREFIX}{question_id}.{level}."
    if lead is None:
        why = _text(f"{PREFIX}why.quiet")
        based_on = None
    else:
        theme = str(lead["key"])
        why = _text(base + "why").format(theme=THEME_PLAIN[theme])
        based_on = {
            "theme": theme,
            "label": lead.get("label"),
            "level_label": LEVEL_LABELS.get(str(lead.get("level")), ""),
            "technical_note": lead.get("technical_note"),
            "evidence_ids": list(lead.get("evidence_ids") or []),
        }
    return Answer(
        question_id=question_id,
        question=question,
        say=_text(base + "say"),
        why=why,
        try_today=_text(base + "try"),
        can_send=send,
        refusal=False,
        based_on=based_on,
    )
