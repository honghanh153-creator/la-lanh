"""Machine-checkable items of the content standard's psychology checklist for framed Tarot
readings (US-20 AC14, B2-4b).

Source: docs/foundation/la-lanh-plain-vietnamese-content-standard.md, "Checklist tâm lý".
Gated by ``tarot:audit``: no advice in the headline, no coercion in authored prose, the reading
ends on the step (advice) and its summary ends on that step. Reported for the owner, not gated:
how many pitfall/cost ideas a map carries, example scenes with advice words, and step actions
with a "khi…" trigger. The rest of the checklist is the owner's reading of the samples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domains.readings.review_agent import ContentReviewAgent
from app.domains.tarot import roles, stance
from app.domains.tarot.engine import _authored_by_engine, _shown_step
from app.domains.tarot.models import TarotReading

# Advice in a headline; the stance markers (statements of the lean) are removed first.
HEADLINE_ADVICE = re.compile(r"\b(?:hãy|nên|đừng|khoan|phải|thử)\b", re.IGNORECASE)
# "Không ra lệnh": no forcing, no consequence or fate attached. Only the explicitly negated force
# "không ai bắt bạn phải" (the approved gentle opener) is exempt; "Lá bắt bạn phải…" is not.
COERCION = re.compile(
    r"(?<!không ai bắt )\bbạn phải\b|\bnhất định\b|\bnếu không thì\b"
    r"|(?<!không )\bbắt buộc\b",
    re.IGNORECASE,
)
SCENE_ADVICE = re.compile(r"\b(?:hãy|thử|nên|đừng)\b", re.IGNORECASE)
TRIGGER = re.compile(r"\bkhi\b", re.IGNORECASE)


@dataclass(frozen=True)
class ChecklistResult:
    headline_advice: bool
    coercion: bool
    ends_with_step: bool
    summary_ends_with_step: bool
    negative_ideas: int
    scenes_with_advice_words: int
    step_action_has_trigger: bool

    @property
    def gated_ok(self) -> bool:
        return (
            not self.headline_advice
            and not self.coercion
            and self.ends_with_step
            and self.summary_ends_with_step
        )


def _alternation(values: list[str]) -> str:
    return "|".join(re.escape(value) for value in sorted(values, key=len, reverse=True))


def _template_patterns() -> tuple[re.Pattern[str], ...]:
    """Each approved headline frame as a full-match pattern: approved action phrases for
    {action}, approved topic phrases for {topic} (no card names since renderer v9)."""

    actions = _alternation([*stance.ACTION_PHRASES.values(), stance.GENERIC_ACTION])
    topics = _alternation(list(stance.TOPIC_PHRASES.values()))
    slots = {
        "{action}": f"(?:{actions})",
        "{topic}": f"(?:{topics})",
        "{target}": f"(?:{actions}|cho (?:{topics}))",
    }
    patterns = []
    for table in (stance.HEADLINES, stance.ROAST_HEADLINES):
        for frames in table.values():
            for template in frames:
                parts = re.split(r"(\{[a-z]+\})", template)
                body = "".join(slots.get(part, re.escape(part)) for part in parts)
                patterns.append(re.compile(body))
    return tuple(patterns)


_TEMPLATES = _template_patterns()


def text_gives_advice(text: str) -> bool:
    """Advice words outside the stance markers (which state the lean, not advise)."""

    lowered = text.lower()
    for marker in stance.MARKERS.values():
        lowered = lowered.replace(marker, " ")
    return bool(HEADLINE_ADVICE.search(lowered))


def template_gives_advice(template: str) -> bool:
    """A headline frame with its slots blanked: the frame's own words must not advise."""

    return text_gives_advice(re.sub(r"\{[a-z]+\}", " ", template))


def headline_gives_advice(headline: str) -> bool:
    """A headline that is exactly an approved frame (its words checked by
    ``template_gives_advice``) filled with approved slot values names what is weighed
    ("trước khi thử lại") without advising it. Anything else is scanned in full."""

    if any(pattern.fullmatch(headline) for pattern in _TEMPLATES):
        return False
    return text_gives_advice(headline)


def check(reading: TarotReading) -> ChecklistResult:
    last = reading.positions[-1]
    sentences = ContentReviewAgent._sentences(reading.summary)
    negative = 0
    for position in reading.positions:
        field = roles.ROLES[position.key].field
        negative += field in {roles.RoleField.TENSION, roles.RoleField.OPTION}
    return ChecklistResult(
        headline_advice=headline_gives_advice(reading.headline),
        coercion=bool(COERCION.search(_authored_by_engine(reading))),
        ends_with_step=last.key in roles.STEP_ROLES and bool(last.small_action),
        summary_ends_with_step=bool(sentences)
        and reading.summary.endswith(stance.step_sentence(_shown_step(reading.positions) or "")),
        negative_ideas=negative,
        scenes_with_advice_words=sum(
            bool(SCENE_ADVICE.search(position.everyday_scene)) for position in reading.positions
        ),
        step_action_has_trigger=bool(TRIGGER.search(last.small_action or "")),
    )
