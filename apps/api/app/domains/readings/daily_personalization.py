"""Bounded editorial interpretations of known factors, never a uniqueness lottery.

Canonical IDs encode facts. Only those fact slots are decoded; orb text, provenance,
evidence identifiers and chart hashes are not personality inputs. Astrology supplies
an editorial angle, not evidence that a hypothetical scene occurred.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domains.astro.models import TimePrecision
from app.domains.content.copy_approval import approved_copy
from app.domains.readings.house_meanings import HOUSE_MEANINGS, many_doors
from app.domains.readings.models import (
    DerivedFactor,
    FactorConfidence,
    FactorKind,
    FactorRole,
    ReadingDomain,
    ReadingPlan,
    SemanticArena,
)

PERSONALIZATION_VERSION = "daily-semantic-eligibility-v6"

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
# US-21 AC07 (modality, "tính chất"): a birth date alone also gives the Sun sign's modality, which
# is coarser than the sign. Cardinal signs start things and change the plan, fixed signs hold on
# and keep things to themselves, mutable signs spread over many things at once. Ordered cardinal,
# fixed, mutable. Chosen so that no sign is left with a single situation: the four signs whose own
# and element situations coincide (aries, taurus, cancer, aquarius) each get a second one from
# their modality. Mutable is not "decision-fatigue": two of its six headlines say the reader is
# tired, and the persona run (#777) saw them on more "Rực"/"Chill" days.
SUN_MODALITY_ISSUES = ("changed-plan", "name-the-need", "too-many-open-loops")
SIGN_MODALITIES = {
    "aries": 0,
    "cancer": 0,
    "libra": 0,
    "capricorn": 0,
    "taurus": 1,
    "leo": 1,
    "scorpio": 1,
    "aquarius": 1,
    "gemini": 2,
    "virgo": 2,
    "sagittarius": 2,
    "pisces": 2,
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
# Date-only pool widening (#841 follow-up): a birth date alone gives 2-3 situations (sign, element,
# modality), so a date-only reader met the same topic within three days on 58% of days. Each sign
# gets one or two more angles of its own, chosen from groups the sign lacks, so every pool holds 4.
# Each sentence waits in the copy registry as ``situation.sun.<sign>.<issue>``; pending = not used.
SUN_EXTRA_ISSUES: dict[str, tuple[str, ...]] = {
    "aries": (
        "comparison-loop",
        "too-many-open-loops",
    ),
    "taurus": (
        "capacity-before-agreement",
        "decision-fatigue",
    ),
    "gemini": (
        "quick-reply",
        "missing-context",
    ),
    "cancer": (
        "name-the-need",
        "avoid-small-conflict",
    ),
    "leo": ("comparison-loop",),
    "virgo": ("decision-fatigue",),
    "libra": ("decision-fatigue",),
    "scorpio": (
        "defend-old-choice",
        "missing-context",
    ),
    "sagittarius": ("repair-reply",),
    "capricorn": ("comparison-loop",),
    "aquarius": (
        "changed-plan",
        "specific-feedback",
    ),
    "pisces": ("avoid-small-conflict",),
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


@dataclass(frozen=True)
class RegistryPairRule:
    """A pair angle whose tendency sentence lives in the copy registry (plan 2026-11-21, #841).

    It applies only once Codex has approved the sentence, so a pending rule never reaches a Daily
    note. ``kind`` is "tense" (square, opposition), "coop" (trine, sextile) or "conj". Only pairs
    without a ``PAIR_RULES`` entry are listed, so an approved rule never changes an existing one.
    """

    bodies: frozenset[str]
    kind: str
    issue: str
    copy_id: str


# Daily pool widening (#841 follow-up): most salient transit contacts have no pair rule, so a chart
# supports two situations on most days. Group "needs" (name-the-need) was the thinnest: eligible on
# 14% of persona-days. These are the most frequent tense contacts that classically read as an
# unspoken need; each sentence is pending in the copy registry.
REGISTRY_PAIR_RULES: tuple[RegistryPairRule, ...] = (
    RegistryPairRule(
        frozenset({"moon", "neptune"}),
        "tense",
        "name-the-need",
        "situation.pair.moon-neptune.tense",
    ),
    RegistryPairRule(
        frozenset({"moon", "uranus"}), "tense", "name-the-need", "situation.pair.moon-uranus.tense"
    ),
    RegistryPairRule(
        frozenset({"moon", "saturn"}), "tense", "name-the-need", "situation.pair.moon-saturn.tense"
    ),
    RegistryPairRule(
        frozenset({"moon", "sun"}), "tense", "name-the-need", "situation.pair.moon-sun.tense"
    ),
    RegistryPairRule(
        frozenset({"moon", "venus"}), "tense", "name-the-need", "situation.pair.moon-venus.tense"
    ),
    # Group "self-judgment" (comparison-loop, perfect-before-start): eligible on 19% of
    # persona-days. Frequent tense Sun contacts read as measuring oneself against others, and
    # Pluto on Mercury as polishing words before letting them go.
    RegistryPairRule(
        frozenset({"chiron", "sun"}), "tense", "comparison-loop", "situation.pair.chiron-sun.tense"
    ),
    RegistryPairRule(
        frozenset({"pluto", "sun"}), "tense", "comparison-loop", "situation.pair.pluto-sun.tense"
    ),
    RegistryPairRule(
        frozenset({"jupiter", "sun"}),
        "tense",
        "comparison-loop",
        "situation.pair.jupiter-sun.tense",
    ),
    RegistryPairRule(
        frozenset({"mercury", "pluto"}),
        "tense",
        "perfect-before-start",
        "situation.pair.mercury-pluto.tense",
    ),
    # Group "overload": decision-fatigue (8%) and capacity-before-agreement (7%) were thin. Tense
    # Mars contacts with Uranus, Neptune and the Sun read as drive pulled in too many directions.
    RegistryPairRule(
        frozenset({"mars", "uranus"}),
        "tense",
        "too-many-open-loops",
        "situation.pair.mars-uranus.tense",
    ),
    RegistryPairRule(
        frozenset({"mars", "neptune"}),
        "tense",
        "decision-fatigue",
        "situation.pair.mars-neptune.tense",
    ),
    RegistryPairRule(
        frozenset({"mars", "sun"}),
        "tense",
        "capacity-before-agreement",
        "situation.pair.mars-sun.tense",
    ),
    # Group "friction": changed-plan (8%) was thin. Tense contacts of Uranus and Pluto with the
    # Sun and Venus read as changing or holding on to a plan, and Sun-Venus as giving way.
    RegistryPairRule(
        frozenset({"sun", "uranus"}), "tense", "changed-plan", "situation.pair.sun-uranus.tense"
    ),
    RegistryPairRule(
        frozenset({"uranus", "venus"}),
        "tense",
        "changed-plan",
        "situation.pair.uranus-venus.tense",
    ),
    RegistryPairRule(
        frozenset({"pluto", "venus"}),
        "tense",
        "defend-old-choice",
        "situation.pair.pluto-venus.tense",
    ),
    RegistryPairRule(
        frozenset({"sun", "venus"}),
        "tense",
        "avoid-small-conflict",
        "situation.pair.sun-venus.tense",
    ),
    # Trines and sextiles (#841 follow-up): the most frequent cooperative transit contacts without
    # a rule. Each reads as a strength that tips into a Daily situation, never as an event.
    RegistryPairRule(
        frozenset({"jupiter", "sun"}),
        "coop",
        "specific-feedback",
        "situation.pair.jupiter-sun.coop",
    ),
    RegistryPairRule(
        frozenset({"jupiter", "mercury"}),
        "coop",
        "too-many-open-loops",
        "situation.pair.jupiter-mercury.coop",
    ),
    RegistryPairRule(
        frozenset({"jupiter", "moon"}),
        "coop",
        "automatic-caretaking",
        "situation.pair.jupiter-moon.coop",
    ),
    RegistryPairRule(
        frozenset({"sun", "uranus"}),
        "coop",
        "changed-plan",
        "situation.pair.sun-uranus.coop",
    ),
    RegistryPairRule(
        frozenset({"moon", "pluto"}),
        "coop",
        "name-the-need",
        "situation.pair.moon-pluto.coop",
    ),
    RegistryPairRule(
        frozenset({"moon", "saturn"}),
        "coop",
        "capacity-before-agreement",
        "situation.pair.moon-saturn.coop",
    ),
    RegistryPairRule(
        frozenset({"neptune", "sun"}),
        "coop",
        "group-pressure",
        "situation.pair.neptune-sun.coop",
    ),
    RegistryPairRule(
        frozenset({"neptune", "venus"}),
        "coop",
        "missing-context",
        "situation.pair.neptune-venus.coop",
    ),
    RegistryPairRule(
        frozenset({"mars", "pluto"}),
        "coop",
        "defend-old-choice",
        "situation.pair.mars-pluto.coop",
    ),
)


def _registry_pair(bodies: frozenset[str], kind: str) -> tuple[str, str] | None:
    """(issue, approved sentence) of the registry rule for ``bodies`` and ``kind``, if approved."""

    for rule in REGISTRY_PAIR_RULES:
        if rule.bodies == bodies and rule.kind == kind:
            text = approved_copy(rule.copy_id)
            return (rule.issue, text) if text else None
    return None


# Which Daily scene a house door may open (plan 1.1, N-4 under the source rule). Only doors a
# classical source stands behind and that are not ⚠ are tagged, so a modern-only door (love in
# house 5) or a ⚠ door (children) never picks the scene. A door with no everyday scene is absent.
DOOR_ARENAS: dict[str, SemanticArena] = {
    "body_appearance": SemanticArena.ENERGY,
    "vitality": SemanticArena.ENERGY,
    "money_wealth": SemanticArena.WORK,
    "gain_loss": SemanticArena.WORK,
    "siblings": SemanticArena.RELATIONSHIPS,
    "messages_news": SemanticArena.COMMUNICATION,
    "everyday_learning": SemanticArena.WORK,
    "home_dwelling": SemanticArena.SELF_CARE,
    "pleasure_feasts": SemanticArena.SELF_CARE,
    "love": SemanticArena.RELATIONSHIPS,
    "business_partners": SemanticArena.RELATIONSHIPS,
    "open_opponents": SemanticArena.RELATIONSHIPS,
    "shared_money": SemanticArena.RELATIONSHIPS,
    "higher_learning": SemanticArena.WORK,
    "career": SemanticArena.WORK,
    "reputation": SemanticArena.WORK,
    "position": SemanticArena.WORK,
    "friends": SemanticArena.RELATIONSHIPS,
    "trust": SemanticArena.RELATIONSHIPS,
    "rest_sleep": SemanticArena.SELF_CARE,
}


@dataclass(frozen=True)
class HouseContext:
    """One house as a Daily situation sees it: its own doors, never a shared group label."""

    house: int
    doors: tuple[str, ...]
    arenas: tuple[SemanticArena, ...]


def _house_context(house: int) -> HouseContext:
    doors = tuple(meaning.key for meaning in many_doors(house))
    arenas = tuple(dict.fromkeys(DOOR_ARENAS[key] for key in doors if key in DOOR_ARENAS))
    return HouseContext(house, doors, arenas)


HOUSE_ARENAS: dict[int, HouseContext] = {house: _house_context(house) for house in HOUSE_MEANINGS}


@dataclass(frozen=True)
class SupportedSituation:
    issue_key: str
    meaning: str
    factor_refs: tuple[str, ...]
    rule_key: str
    rank: tuple[int, int, int]
    house: HouseContext | None = None

    @property
    def arenas(self) -> tuple[SemanticArena, ...]:
        return self.house.arenas if self.house else ()


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
        if factor.kind is FactorKind.DATE_ONLY_VIBE and plan.daily_variety is not None:
            # US-21 AC07: a birth date alone still supports the Sun's element, so a
            # date-only Daily has a second situation to rotate with. It rests on the
            # same Sun factor (no Moon, angle or house) and ranks below the sign's own
            # situation. Plans without the daily rotation never get it: the lens filter
            # runs before ranking, so a lower rank alone would let it replace the
            # fallback those plans had when the lens excludes the sign's situation.
            element_key = PLACEMENT_ISSUES["sun"][SIGN_ELEMENTS[sign]]
            if element_key != key:
                situations.append(
                    SupportedSituation(
                        element_key,
                        PLACEMENT_MEANINGS[element_key],
                        (factor.id,),
                        f"element-sun-{sign}",
                        (role_priority, 0, int(factor.strength * 4) - 1),
                    )
                )
            # US-21 AC07: the sign's modality is a third situation on the same Sun factor, ranked
            # below the element's. It is left out when it repeats one already in the pool.
            modality_key = SUN_MODALITY_ISSUES[SIGN_MODALITIES[sign]]
            if modality_key not in {key, element_key}:
                situations.append(
                    SupportedSituation(
                        modality_key,
                        PLACEMENT_MEANINGS[modality_key],
                        (factor.id,),
                        f"modality-sun-{sign}",
                        (role_priority, 0, int(factor.strength * 4) - 2),
                    )
                )
            # More angles of the sign, once their sentence is approved, ranked below the modality.
            shown = {key, element_key, modality_key}
            for step, extra_key in enumerate(SUN_EXTRA_ISSUES.get(sign, ()), start=3):
                sentence = approved_copy(f"situation.sun.{sign}.{extra_key}")
                if sentence and extra_key not in shown:
                    shown.add(extra_key)
                    situations.append(
                        SupportedSituation(
                            extra_key,
                            sentence,
                            (factor.id,),
                            f"extra-sun-{sign}-{extra_key}",
                            (role_priority, 0, int(factor.strength * 4) - step),
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
        bodies = frozenset({body_a, body_b})
        rule = next((rule for rule in PAIR_RULES if rule.bodies == bodies), None)
        if rule is None and not any(item.bodies == bodies for item in REGISTRY_PAIR_RULES):
            continue
        children = [by_id[ref] for ref in factor.child_refs if ref in by_id]
        if any(child.kind is not FactorKind.PLANET_PLACEMENT for child in children):
            continue
        if not transit and {child.subjects[0] for child in children} != bodies:
            continue
        if transit and not any(child.subjects[0] == body_b for child in children):
            continue
        tense = aspect in {"square", "opposition"} and (
            transit or factor.role is FactorRole.TENSION
        )
        cooperative = aspect in {"trine", "sextile"} and (
            transit or factor.role in {FactorRole.SUPPORTING, FactorRole.REINFORCEMENT}
        )
        if rule is None:
            # A registry rule: its own kind, and only with an approved sentence.
            kind = "tense" if tense else "coop" if cooperative else None
            if (
                kind is None
                and aspect == "conjunction"
                and (transit or factor.role in {FactorRole.SUPPORTING, FactorRole.REINFORCEMENT})
            ):
                kind = "conj"
            approved = _registry_pair(bodies, kind) if kind else None
            if approved is None:
                continue
            key, meaning = approved
        else:
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
            topic not in HOUSE_ARENAS[int(factor.id.split(":")[3])].arenas,
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
