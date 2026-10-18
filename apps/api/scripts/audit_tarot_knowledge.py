from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.domains.tarot import question_frame
from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.knowledge import BOOK_SOURCES, all_cards
from app.domains.tarot.models import (
    TarotContext,
    TarotQuestionForm,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)

QUESTION_BANK = Path(__file__).resolve().parents[3] / "docs/fixtures/tarot-question-bank-v1.json"
FORM_ACCURACY_FLOOR = 0.95  # US-20 AC01

QUESTION_BY_CONTEXT = {
    TarotContext.GENERAL: "Chuyện này cần được nhìn từ góc nào trước?",
    TarotContext.RELATIONSHIPS: "Giữa tụi mình, điều gì đáng hỏi thẳng thay vì tiếp tục đoán?",
    TarotContext.WORK: "Mình cần nói rõ điều gì trước khi nhận thêm việc?",
    TarotContext.COMMUNICATION: "Trong cuộc nói chuyện này, điều gì đáng hỏi lại cho rõ?",
    TarotContext.ENERGY: "Điều gì đang tiêu hao nhiều hơn giá trị nó trả lại?",
    TarotContext.SELF_CARE: "Nhu cầu nào của mình đang bị xếp sau mọi người?",
}

FORBIDDEN = {
    "tín hiệu vũ trụ",
    "vũ trụ thì thầm",
    "mọi thứ xảy ra đều có lý do",
    "hãy tin vào hành trình",
    "năng lượng đang dịch chuyển",
}

GOAL_QUESTIONS = (
    (TarotContext.RELATIONSHIPS, "Mình nên nói gì để xin lỗi sau khi lỡ hẹn?"),
    (TarotContext.RELATIONSHIPS, "Mình nên nói gì để thống nhất lịch gặp?"),
    (TarotContext.RELATIONSHIPS, "Mình nên nói gì để cả hai cùng quan tâm nhau?"),
    (TarotContext.WORK, "Mình nên nói gì để chia việc và bàn giao rõ hơn?"),
    (TarotContext.WORK, "Mình nên nói gì để công sức được ghi nhận?"),
    (TarotContext.WORK, "Mình cần nói rõ điều gì trước khi nhận thêm việc?"),
    (TarotContext.ENERGY, "Mình nên nghỉ thế nào khi đang mệt?"),
    (TarotContext.COMMUNICATION, "Mình nên nói gì khi hai bên bất đồng?"),
)


def audit() -> list[str]:
    failures: list[str] = []
    cards = all_cards()
    if len(cards) != 78 or len({card.id for card in cards}) != 78:
        failures.append("Deck must contain exactly 78 unique cards")
    if len(BOOK_SOURCES) != 8 or len({source.source_id for source in BOOK_SOURCES}) != 8:
        failures.append("Tarot methodology must have exactly eight unique launch sources")
    if any(not source.allowed_uses or not source.prohibited_uses for source in BOOK_SOURCES):
        failures.append("Every source needs explicit allowed and prohibited use notes")

    engine = TarotReadingEngine()
    semantic_blocks: Counter[str] = Counter()
    for context in TarotContext:
        for card in cards:
            reading = engine.render(
                card_ids=(card.id,),
                spread=TarotSpread.ONE_CARD,
                context=context,
                question=QUESTION_BY_CONTEXT[context],
                voice=TarotVoice.PLAYFUL_GROUNDED,
            )
            position = reading.positions[0]
            blocks = (
                position.meaning_here,
                position.everyday_scene,
                position.reflection_question,
                position.small_action or "",
            )
            semantic_blocks.update(
                (
                    position.meaning_here,
                    position.everyday_scene,
                    position.small_action or "",
                )
            )
            joined = " ".join((reading.headline, reading.summary, *blocks)).casefold()
            if any(fragment in joined for fragment in FORBIDDEN):
                failures.append(f"Forbidden filler in {context.value}/{card.id}")
            if not reading.provenance.source_ids:
                failures.append(f"Missing provenance in {context.value}/{card.id}")
            if any(len(block.split()) < 7 for block in blocks):
                failures.append(f"Thin semantic block in {context.value}/{card.id}")

        sample_ids = tuple(card.id for card in cards[:3])
        spread = engine.render(
            card_ids=sample_ids,
            spread=TarotSpread.THREE_CARD,
            context=context,
            question=QUESTION_BY_CONTEXT[context],
            voice=TarotVoice.PLAYFUL_GROUNDED,
        )
        if len({position.meaning_here for position in spread.positions}) != 3:
            failures.append(f"Three-card meanings repeat in {context.value}")
        if len({position.small_action for position in spread.positions}) != 3:
            failures.append(f"Three-card actions repeat in {context.value}")

    repeated = [block for block, count in semantic_blocks.items() if count > len(cards)]
    if repeated:
        failures.append("A complete semantic block repeats across more than one full deck")
    # Rotate every card through every position, context and existing voice, on both renderer
    # paths: legacy sessions (no QuestionFrame) and framed sessions read by role (B2-2).
    # This is deterministic synthetic coverage, not a human comprehension study.
    frames = {
        question: engine.assess_question(question, context).frame
        for context, question in (*QUESTION_BY_CONTEXT.items(), *GOAL_QUESTIONS)
    }
    for spread_map in TarotSpreadMap:
        count = len(engine.positions_for(spread_map))
        selected_spread = {
            1: TarotSpread.ONE_CARD,
            3: TarotSpread.THREE_CARD,
            5: TarotSpread.FIVE_CARD,
        }[count]
        for context in TarotContext:
            for voice in TarotVoice:
                for offset in range(len(cards)):
                    card_ids = tuple(
                        cards[(offset + index) % len(cards)].id for index in range(count)
                    )
                    question = QUESTION_BY_CONTEXT[context]
                    for frame in (None, frames[question]):
                        try:
                            engine.render(
                                card_ids=card_ids,
                                spread=selected_spread,
                                spread_map=spread_map,
                                context=context,
                                question=question,
                                voice=voice,
                                frame=frame,
                            )
                        except TarotContentRejected as exc:
                            path = "role" if frame else "legacy"
                            failures.append(
                                f"{path}/{spread_map.value}/{context.value}/{voice.value}/"
                                f"{offset}: {exc}"
                            )
        for context, question in GOAL_QUESTIONS:
            for voice in TarotVoice:
                for offset in range(len(cards)):
                    for frame in (None, frames[question]):
                        try:
                            engine.render(
                                card_ids=tuple(
                                    cards[(offset + index) % len(cards)].id
                                    for index in range(count)
                                ),
                                spread=selected_spread,
                                spread_map=spread_map,
                                context=context,
                                question=question,
                                voice=voice,
                                frame=frame,
                            )
                        except TarotContentRejected as exc:
                            path = "role" if frame else "legacy"
                            failures.append(
                                f"{path}/goal/{question}/{spread_map.value}/{offset}: {exc}"
                            )
    return failures


def audit_question_bank() -> tuple[list[str], dict[str, Any]]:
    """B2-1 question understanding on the synthetic bank (US-20 AC01-AC05)."""

    engine = TarotReadingEngine()
    items: list[dict[str, Any]] = json.loads(QUESTION_BANK.read_text())["items"]
    failures: list[str] = []
    labelled = [item for item in items if item.get("form")]
    wrong = [
        item["id"]
        for item in labelled
        if question_frame.classify_form(item["question"]).value != item["form"]
    ]
    accuracy = 1 - len(wrong) / len(labelled)
    if accuracy < FORM_ACCURACY_FLOOR:
        failures.append(f"form accuracy {accuracy:.4f} < {FORM_ACCURACY_FLOOR}: {wrong[:10]}")
    actions: Counter[str] = Counter()
    for item in items:
        context = TarotContext(item["context"]) if item.get("context") else TarotContext.GENERAL
        assessment = engine.assess_question(item["question"], context)
        if assessment.accepted is not item["expected"]["accepted"]:
            failures.append(f"{item['id']}: accepted={assessment.accepted}")
            continue
        if not assessment.accepted:
            if not assessment.suggested_reframe:
                failures.append(f"{item['id']}: rejection without a reframe")
            continue
        frame = assessment.frame
        if frame is None:
            failures.append(f"{item['id']}: accepted without a frame")
            continue
        actions[frame.action.value if frame.action else "none"] += 1
        expected_topic = item["expected"].get("topic")
        if expected_topic and frame.topic.value != expected_topic:
            failures.append(f"{item['id']}: topic {frame.topic.value} != {expected_topic}")
        if frame.form is TarotQuestionForm.TIMING:
            reading = engine.render(
                card_ids=(all_cards()[0].id,),
                spread=TarotSpread.ONE_CARD,
                context=context,
                question=item["question"],
                voice=TarotVoice.STRAIGHT_WARM,
                question_intent=assessment.intent,
                frame=frame,
            )
            if not reading.summary.startswith(question_frame.READINESS_NOTE):
                failures.append(f"{item['id']}: timing question without the readiness note")
    metrics = {
        "labelled": len(labelled),
        "form_accuracy": round(accuracy, 4),
        "actions_matched": sum(n for k, n in actions.items() if k != "none"),
        "actions_none": actions["none"],
        "action_labels_used": len([k for k in actions if k != "none"]),
    }
    return failures, metrics


HEADLINE_DUPLICATE_CEILING = 0.10  # US-20 AC11
_DIRECT_VOICES = (TarotVoice.STRAIGHT_WARM, TarotVoice.GENTLE_SPECIFIC, TarotVoice.PLAYFUL_GROUNDED)


def audit_stance_and_headlines() -> tuple[list[str], dict[str, Any]]:
    """B2-3 on the bank: stance distribution, headline duplicates (< 10%), no generic copy.

    Every accepted bank question x every spread map x the three direct voices, with cards drawn
    from a seed fixed per question (the Roast headline is B2-4).
    """

    import random

    from app.domains.tarot import roles as tarot_roles

    engine = TarotReadingEngine()
    items: list[dict[str, Any]] = json.loads(QUESTION_BANK.read_text())["items"]
    cards = [card.id for card in all_cards()]
    headlines: dict[TarotVoice, list[str]] = {voice: [] for voice in _DIRECT_VOICES}
    levels: Counter[str] = Counter()
    generic = 0
    failures: list[str] = []
    for item in items:
        if not item["expected"]["accepted"]:
            continue
        context = TarotContext(item["context"])
        assessment = engine.assess_question(item["question"], context)
        rng = random.Random(f"tarot-b2-3-{item['id']}")  # noqa: S311 - synthetic sampling
        for spread_map in TarotSpreadMap:
            count = len(engine.positions_for(spread_map))
            ids = tuple(rng.sample(cards, count))
            spread = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
            for voice in _DIRECT_VOICES:
                try:
                    reading = engine.render(
                        card_ids=ids,
                        spread=spread[count],
                        spread_map=spread_map,
                        context=context,
                        question=item["question"],
                        voice=voice,
                        question_intent=assessment.intent,
                        frame=assessment.frame,
                    )
                except TarotContentRejected as exc:
                    failures.append(f"stance/{item['id']}/{spread_map.value}/{voice.value}: {exc}")
                    continue
                # Measurement spec §4c T2: normalised, per voice.
                headlines[voice].append(" ".join(reading.headline.casefold().split()).rstrip(".!?"))
                levels[reading.stance.level.value if reading.stance else "none"] += 1
                prose = " ".join(
                    [reading.headline, reading.summary]
                    + [p.meaning_here + " " + (p.small_action or "") for p in reading.positions]
                ).casefold()
                generic += any(prefix in prose for prefix in tarot_roles.RETIRED_PREFIXES)
    rates = {
        voice.value: round(1 - len(set(values)) / len(values), 4) if values else 0.0
        for voice, values in headlines.items()
    }
    duplicate_rate = max(rates.values())
    if duplicate_rate >= HEADLINE_DUPLICATE_CEILING:
        failures.append(f"headline duplicate rate {rates} >= 0.10")
    if generic:
        failures.append(f"{generic} framed readings still carry generic filler")
    metrics = {
        "readings": sum(len(values) for values in headlines.values()),
        "headline_duplicate_rate": rates,
        "stance_levels": dict(sorted(levels.items())),
        "generic": generic,
    }
    return failures, metrics


def main() -> None:
    failures = audit()
    stance_failures, stance_metrics = audit_stance_and_headlines()
    failures += stance_failures
    bank_failures, bank = audit_question_bank()
    failures += bank_failures
    if failures:
        raise SystemExit("Tarot knowledge audit failed:\n- " + "\n- ".join(failures[:30]))
    per_voice = len(TarotSpreadMap) * len(all_cards())
    contextual = per_voice * len(TarotContext) * len(TarotVoice)
    goals = per_voice * len(GOAL_QUESTIONS) * len(TarotVoice)
    print(
        f"Tarot knowledge audit passed: {contextual} contextual + {goals} recognised-goal "
        f"synthetic spreads across {len(TarotVoice)} voices (including roast), each on the legacy "
        "and the role (B2-2) renderer, plus deck checks. "
        "Not a human comprehension study."
    )
    print(
        f"Question bank (B2-1): form accuracy {bank['form_accuracy']} on {bank['labelled']} "
        f"labelled; closed action label on {bank['actions_matched']} accepted questions, none on "
        f"{bank['actions_none']} ({bank['action_labels_used']} of 30 labels used)."
    )
    print(
        f"Stance and headlines (B2-3): {stance_metrics['readings']} framed readings; headline "
        f"duplicate rate {stance_metrics['headline_duplicate_rate']}; stance levels "
        f"{stance_metrics['stance_levels']}; generic filler {stance_metrics['generic']}."
    )


if __name__ == "__main__":
    main()
