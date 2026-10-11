from __future__ import annotations

from collections import Counter

from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.knowledge import BOOK_SOURCES, all_cards
from app.domains.tarot.models import TarotContext, TarotSpread, TarotSpreadMap, TarotVoice

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
                position.small_action,
            )
            semantic_blocks.update(
                (
                    position.meaning_here,
                    position.everyday_scene,
                    position.small_action,
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
    # Rotate every card through every position, context and existing voice.
    # This is deterministic synthetic coverage, not a human comprehension study.
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
                    try:
                        engine.render(
                            card_ids=card_ids,
                            spread=selected_spread,
                            spread_map=spread_map,
                            context=context,
                            question=QUESTION_BY_CONTEXT[context],
                            voice=voice,
                        )
                    except TarotContentRejected as exc:
                        failures.append(
                            f"{spread_map.value}/{context.value}/{voice.value}/{offset}: {exc}"
                        )
        for context, question in GOAL_QUESTIONS:
            for voice in TarotVoice:
                for offset in range(len(cards)):
                    try:
                        engine.render(
                            card_ids=tuple(
                                cards[(offset + index) % len(cards)].id for index in range(count)
                            ),
                            spread=selected_spread,
                            spread_map=spread_map,
                            context=context,
                            question=question,
                            voice=voice,
                        )
                    except TarotContentRejected as exc:
                        failures.append(f"goal/{question}/{spread_map.value}/{offset}: {exc}")
    return failures


def main() -> None:
    failures = audit()
    if failures:
        raise SystemExit("Tarot knowledge audit failed:\n- " + "\n- ".join(failures[:30]))
    print(
        "Tarot knowledge audit passed: 8424 contextual + 11232 recognised-goal synthetic spreads, "
        "plus deck checks. Not a human comprehension study."
    )


if __name__ == "__main__":
    main()
