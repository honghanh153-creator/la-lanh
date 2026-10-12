"""Bounded editorial interpretations of known factors, never a uniqueness lottery.

Canonical IDs encode facts. Only those fact slots are decoded; orb text, provenance,
evidence identifiers and chart hashes are not personality inputs. Astrology supplies
an editorial angle, not evidence that a hypothetical scene occurred.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.astro.models import TimePrecision
from app.domains.readings.models import (
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    ReadingDomain,
    ReadingPlan,
    SemanticArena,
)

PERSONALIZATION_VERSION = "daily-semantic-eligibility-v4"

# Sun-only angles follow the existing sign catalog's distinct stresses, not a
# numeric offset into unrelated situations. They remain general editorial lenses.
SUN_ISSUES = {
    "aries": "quick-reply",
    "taurus": "defend-old-choice",
    "gemini": "too-many-open-loops",
    "cancer": "automatic-caretaking",
    "leo": "specific-feedback",
    "virgo": "perfect-before-start",
    "libra": "avoid-small-conflict",
    "scorpio": "name-the-need",
    "sagittarius": "changed-plan",
    "capricorn": "capacity-before-agreement",
    "aquarius": "group-pressure",
    "pisces": "missing-context",
}

# Ordered fire, earth, air, water. Each choice names a distinct response/action.
PLACEMENT_ISSUES = {
    "sun": ("quick-reply", "defend-old-choice", "group-pressure", "automatic-caretaking"),
    "moon": ("quick-reply", "decision-fatigue", "missing-context", "automatic-caretaking"),
    "mercury": ("quick-reply", "perfect-before-start", "too-many-open-loops", "missing-context"),
    "venus": ("avoid-small-conflict", "automatic-caretaking", "group-pressure", "missing-context"),
    "mars": ("too-many-open-loops", "defend-old-choice", "quick-reply", "avoid-small-conflict"),
    "jupiter": ("too-many-open-loops",) * 4,
    "saturn": ("perfect-before-start",) * 4,
    "uranus": ("changed-plan",) * 4,
    "neptune": ("missing-context",) * 4,
    "pluto": ("defend-old-choice",) * 4,
}
SIGN_ELEMENTS = {
    "aries": 0,
    "leo": 0,
    "sagittarius": 0,
    "taurus": 1,
    "virgo": 1,
    "capricorn": 1,
    "gemini": 2,
    "libra": 2,
    "aquarius": 2,
    "cancer": 3,
    "scorpio": 3,
    "pisces": 3,
}
BODY_DOMAINS = {
    "sun": ReadingDomain.CORE,
    "moon": ReadingDomain.EMOTIONS,
    "mercury": ReadingDomain.MIND,
    "venus": ReadingDomain.RELATING,
    "mars": ReadingDomain.DRIVE,
    "jupiter": ReadingDomain.CORE,
    "saturn": ReadingDomain.CORE,
    "uranus": ReadingDomain.CORE,
    "neptune": ReadingDomain.EMOTIONS,
    "pluto": ReadingDomain.DRIVE,
}
PLACEMENT_MEANINGS = {
    "quick-reply": "Bạn dễ muốn trả lời nhanh hơn thời gian cần để hiểu rõ.",
    "defend-old-choice": "Bạn dễ muốn giữ cách quen dù cần kiểm tra kết quả mới.",
    "group-pressure": "Bạn dễ muốn hòa cùng mọi người dù còn cần hiểu rõ.",
    "automatic-caretaking": "Bạn dễ muốn giúp người khác dù sức mình có giới hạn.",
    "decision-fatigue": "Bạn cần đủ sức và rõ tiêu chí trước khi chọn.",
    "missing-context": "Bạn dễ muốn hiểu người kia nhưng thông tin còn thiếu.",
    "perfect-before-start": "Bạn dễ muốn làm cho đúng nhưng vẫn cần nhận góp ý.",
    "too-many-open-loops": "Bạn dễ muốn thử thêm việc dù việc trước còn dở.",
    "avoid-small-conflict": "Bạn dễ muốn giữ hòa khí dù có điều mình không muốn nhận.",
    "changed-plan": "Bạn dễ muốn đổi cách làm nhưng vẫn cần thống nhất lịch.",
    "specific-feedback": "Bạn dễ muốn được hiểu đúng qua phản hồi cụ thể.",
    "name-the-need": "Bạn dễ muốn giữ điều riêng nhưng vẫn cần nói rõ nhu cầu.",
    "capacity-before-agreement": "Bạn dễ muốn giữ trách nhiệm nhưng thời gian có giới hạn.",
}


# Context-specific tendencies chosen inside eligible_daily_situations().
CAPACITY_AT_WORK_MEANING = "Bạn muốn giúp trong việc cần làm, nhưng lịch nhận việc có giới hạn."
REPAIR_REPLY_MEANING = "Bạn dễ nhận ra mình vừa trả lời hơi nhanh, sau khi câu đã gửi đi."


@dataclass(frozen=True)
class PairRule:
    bodies: frozenset[str]
    tension_issue: str
    cooperative_issue: str
    tension_meaning: str
    cooperative_meaning: str
    conjunction_issue: str | None = None
    conjunction_meaning: str | None = None


PAIR_RULES = (
    PairRule(
        frozenset({"mercury", "venus"}),
        "group-pressure",
        "specific-feedback",
        "Bạn muốn hiểu cho rõ, nhưng cũng muốn giữ hòa khí khi mọi người đã chốt ý.",
        "Bạn trao đổi tự tin hơn khi biết rõ mình đang được hỏi về phần nào.",
        "specific-feedback",
        "Bạn vừa cần hiểu rõ, vừa cần được người kia hiểu đúng.",
    ),
    PairRule(
        frozenset({"mercury", "saturn"}),
        "perfect-before-start",
        "specific-feedback",
        "Bạn muốn nói cho thật đúng, nên dễ sửa mãi dù đã đủ ý.",
        "Bạn thường chuẩn bị kỹ trước khi đưa việc của mình cho người khác xem.",
    ),
    PairRule(
        frozenset({"mercury", "neptune"}),
        "missing-context",
        "specific-feedback",
        "Bạn muốn hiểu cho rõ, nhưng dễ tự đoán để lấp chỗ thông tin còn thiếu.",
        "Bạn có nhiều ý tưởng, nhưng chúng dễ còn mơ hồ với người nghe.",
    ),
    PairRule(
        frozenset({"venus", "saturn"}),
        "capacity-before-agreement",
        "specific-feedback",
        "Bạn muốn giữ lời với người khác, trong khi thời gian nhận việc có giới hạn.",
        "Bạn coi trọng hợp tác và muốn phần việc của mỗi người thật rõ ràng.",
    ),
    PairRule(
        frozenset({"moon", "mars"}),
        "quick-reply",
        "name-the-need",
        "Bạn dễ phản ứng ngay, trước khi kịp gọi tên cảm giác của mình.",
        "Bạn có nhiều năng lượng để làm, nhưng dễ quên hỏi mình đang cần gì.",
    ),
    PairRule(
        frozenset({"sun", "saturn"}),
        "comparison-loop",
        "specific-feedback",
        "Bạn muốn làm tốt, nên dễ tự chê khi nhìn kết quả của người khác.",
        "Bạn đặt tiêu chuẩn cao cho việc mình làm và muốn biết mình đang ở đâu.",
    ),
    PairRule(
        frozenset({"venus", "mars"}),
        "avoid-small-conflict",
        "name-the-need",
        "Bạn muốn giữ hòa khí, dù vẫn có việc bạn không muốn nhận.",
        "Bạn biết mình muốn gì, nhưng không phải lúc nào cũng nói ra.",
    ),
)

HOUSE_ARENAS = {
    1: SemanticArena.SELF_CARE,
    2: SemanticArena.WORK,
    3: SemanticArena.COMMUNICATION,
    4: SemanticArena.SELF_CARE,
    5: SemanticArena.SELF_CARE,
    6: SemanticArena.ENERGY,
    7: SemanticArena.RELATIONSHIPS,
    8: SemanticArena.RELATIONSHIPS,
    9: SemanticArena.WORK,
    10: SemanticArena.WORK,
    11: SemanticArena.COMMUNICATION,
    12: SemanticArena.SELF_CARE,
}


@dataclass(frozen=True)
class SupportedSituation:
    issue_key: str
    meaning: str
    factor_refs: tuple[str, ...]
    rule_key: str
    rank: tuple[int, int, int]
    arena: SemanticArena | None = None


def eligible_daily_situations(plan: ReadingPlan) -> tuple[SupportedSituation, ...]:
    """Rank by role, supported interaction, then bounded strength, never ID entropy."""
    by_id = {factor.id: factor for factor in plan.factors}
    heroes = set(plan.hero_factor_refs)
    situations: list[SupportedSituation] = []
    for factor in plan.factors:
        parts = factor.id.split(":")
        if factor.kind is FactorKind.DATE_ONLY_VIBE:
            if parts[3] != "certain" or parts[4] not in SIGN_ELEMENTS:
                continue
            body, sign = "sun", parts[4]
        elif factor.kind is FactorKind.PLANET_PLACEMENT:
            body, sign = parts[1], parts[3]
        else:
            continue
        if (
            body not in PLACEMENT_ISSUES
            or sign not in SIGN_ELEMENTS
            or factor.domain is not BODY_DOMAINS[body]
            or factor.subjects != (body,)
        ):
            continue
        key = SUN_ISSUES[sign] if body == "sun" else PLACEMENT_ISSUES[body][SIGN_ELEMENTS[sign]]
        # Mutable Mercury opens more tasks; Libra's social emphasis raises a
        # different question from Gemini's information gathering.
        if body == "mercury" and sign == "libra":
            key = "group-pressure"
        if body == "venus" and sign == "cancer":
            key = "automatic-caretaking"
        meaning = PLACEMENT_MEANINGS[key]
        role_priority = 2 if factor.id in heroes and factor.role is FactorRole.PRIMARY else 1
        if factor.role is FactorRole.FALLBACK:
            role_priority = 0
        refs = [factor.id]
        context = None
        if plan.precision is TimePrecision.EXACT:
            houses = sorted(
                (
                    item
                    for item in plan.factors
                    if item.kind is FactorKind.HOUSE_PLACEMENT
                    and item.subjects[0] == body
                    and factor.id in item.child_refs
                    and item.confidence is FactorConfidence.HIGH
                ),
                key=lambda item: int(item.id.split(":")[3]),
            )
            if houses:
                house = houses[0]
                refs.append(house.id)
                house_number = int(house.id.split(":")[3])
                context = HOUSE_ARENAS[house_number]
                if key == "automatic-caretaking" and house_number in {6, 10}:
                    key = "capacity-before-agreement"
                    meaning = CAPACITY_AT_WORK_MEANING
        situations.append(
            SupportedSituation(
                key,
                meaning,
                tuple(refs),
                f"placement-{body}-{sign}",
                (role_priority, 0, int(factor.strength * 4)),
                context,
            )
        )

    for factor in plan.factors:
        if factor.kind not in {FactorKind.NATAL_ASPECT, FactorKind.TRANSIT_CONTACT}:
            continue
        # A planner-selected moderate conjunction is still evidence for a bounded
        # combined angle. Weak contacts and unselected marginal contacts stay out.
        minimum_strength = 0.25 if factor.id in heroes else 0.35
        if factor.strength < minimum_strength or factor.confidence is FactorConfidence.LIMITED:
            continue
        parts = factor.id.split(":")
        transit = factor.kind is FactorKind.TRANSIT_CONTACT
        body_a, aspect, body_b = [*parts[1:3], parts[4]] if transit else parts[2:5]
        if set(factor.subjects) != {body_a, body_b}:
            continue
        rule = next(
            (rule for rule in PAIR_RULES if rule.bodies == frozenset({body_a, body_b})), None
        )
        if rule is None:
            continue
        children = [by_id[ref] for ref in factor.child_refs if ref in by_id]
        if any(child.kind is not FactorKind.PLANET_PLACEMENT for child in children):
            continue
        if not transit and {child.subjects[0] for child in children} != rule.bodies:
            continue
        if transit and not any(child.subjects[0] == body_b for child in children):
            continue
        tense = aspect in {"square", "opposition"} and (
            transit or factor.role is FactorRole.TENSION
        )
        cooperative = aspect in {"trine", "sextile"} and (
            transit or factor.role in {FactorRole.SUPPORTING, FactorRole.REINFORCEMENT}
        )
        conjunction = (
            aspect == "conjunction"
            and rule.conjunction_issue is not None
            and rule.conjunction_meaning is not None
            and (transit or factor.role in {FactorRole.SUPPORTING, FactorRole.REINFORCEMENT})
        )
        if not tense and not cooperative and not conjunction:
            continue
        if conjunction:
            # Both optional fields are required by the condition above.
            key = rule.conjunction_issue or rule.cooperative_issue
            meaning = rule.conjunction_meaning or rule.cooperative_meaning
        else:
            key = rule.tension_issue if tense else rule.cooperative_issue
            meaning = rule.tension_meaning if tense else rule.cooperative_meaning
        phase = factor.phase.value if factor.phase else _natal_phase(factor)
        if tense and key == "quick-reply" and phase == "separating":
            key = "repair-reply"
            meaning = REPAIR_REPLY_MEANING
        # A transit is secondary to a selected natal interaction, and must be
        # connected to the known natal actor. No calendar/event claim is made.
        priority = 2 if transit else (3 if factor.id in heroes else 1)
        pair_house = _pair_house_context(plan, tuple(child.id for child in children))
        situations.append(
            SupportedSituation(
                key,
                meaning,
                (
                    factor.id,
                    *(child.id for child in children),
                    *((pair_house.id,) if pair_house else ()),
                ),
                f"pair-{body_a}-{aspect}-{body_b}-{phase or 'unknown'}",
                (priority, 1, int(factor.strength * 4)),
                HOUSE_ARENAS[int(pair_house.id.split(":")[3])] if pair_house else None,
            )
        )
    return tuple(situations)


def _pair_house_context(
    plan: ReadingPlan,
    placement_refs: tuple[str, ...],
) -> DerivedFactor | None:
    if plan.precision is not TimePrecision.EXACT:
        return None
    topic = plan.background_lens.value if plan.background_lens else "auto"
    candidates = (
        factor
        for factor in plan.factors
        if factor.kind is FactorKind.HOUSE_PLACEMENT
        and factor.confidence is FactorConfidence.HIGH
        and set(factor.child_refs).intersection(placement_refs)
    )
    # The explicit topic wins, then a stable known house/body ordering. No ID hash.
    return min(
        candidates,
        key=lambda factor: (
            HOUSE_ARENAS[int(factor.id.split(":")[3])].value != topic,
            int(factor.id.split(":")[3]),
            factor.subjects[0],
        ),
        default=None,
    )


def _natal_phase(factor: DerivedFactor) -> str | None:
    first, second = factor.subjects
    prefixes = (
        f"natal:aspect:{first}:{second}:phase:",
        f"natal:aspect:{second}:{first}:phase:",
    )
    phases = {ref.rsplit(":", 1)[1] for ref in factor.evidence_refs if ref.startswith(prefixes)}
    return next(iter(phases)) if len(phases) == 1 and phases <= {"applying", "separating"} else None
