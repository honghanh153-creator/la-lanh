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
from app.domains.tarot.engine import _authored_by_engine, _position_views
from app.domains.tarot.models import TarotReading

# Advice in a headline; the stance markers (statements of the lean) are removed first.
HEADLINE_ADVICE = re.compile(r"\b(?:hãy|nên|đừng|khoan|phải|thử)\b", re.IGNORECASE)
# "Không ra lệnh": no forcing, no consequence or fate attached. A negated force ("không ai bắt
# bạn phải gồng", the gentle opener) is the opposite of coercion and is not matched.
COERCION = re.compile(
    r"(?<!bắt )\bbạn phải\b|\bnhất định\b|\bnếu không thì\b|(?<!không )\bbắt buộc\b",
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


def headline_gives_advice(headline: str) -> bool:
    """Stance markers state the lean and approved action phrases name what is being weighed
    ("trước khi thử lại"); neither is advice, so both are removed before the scan."""

    text = headline.lower()
    for phrase in (*stance.MARKERS.values(), *stance.ACTION_PHRASES.values()):
        text = text.replace(phrase, " ")
    return bool(HEADLINE_ADVICE.search(text))


def check(reading: TarotReading) -> ChecklistResult:
    views = _position_views(reading.positions, reading.context)
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
        summary_ends_with_step=bool(sentences) and stance.anchor(views[-1]) in sentences[-1],
        negative_ideas=negative,
        scenes_with_advice_words=sum(
            bool(SCENE_ADVICE.search(position.everyday_scene)) for position in reading.positions
        ),
        step_action_has_trigger=bool(TRIGGER.search(last.small_action or "")),
    )
