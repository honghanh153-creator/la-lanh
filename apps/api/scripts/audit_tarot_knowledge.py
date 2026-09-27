from __future__ import annotations

from collections import Counter

from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.knowledge import BOOK_SOURCES, all_cards
from app.domains.tarot.models import TarotContext, TarotSpread, TarotVoice

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


def audit() -> list[str]:
    failures: list[str] = []
    cards = all_cards()
    if len(cards) != 78 or len({card.id for card in cards}) != 78:
        failures.append("Deck must contain exactly 78 unique cards")
    if len(BOOK_SOURCES) != 5 or len({source.source_id for source in BOOK_SOURCES}) != 5:
        failures.append("Tarot methodology must have exactly five unique launch sources")
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
            semantic_blocks.update(blocks)
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
    return failures


def main() -> None:
    failures = audit()
    if failures:
        raise SystemExit("Tarot knowledge audit failed:\n- " + "\n- ".join(failures[:30]))
    print("Tarot knowledge audit passed: 78 cards x 6 contexts + three-card samples.")


if __name__ == "__main__":
    main()
