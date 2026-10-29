from __future__ import annotations

import json
import re
import unicodedata
import uuid
from collections import Counter, defaultdict
from math import comb
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


# US-20 AC11 / measurement spec T2, as changed after the owner's feedback of 29/10/2026: headlines
# no longer name cards, so the ceiling applies to the reading's opening (headline + summary), what
# the reader scans first. The headline-only rate is still reported.
OPENING_DUPLICATE_CEILING = 0.10
T4_FLOOR = 0.80  # US-20 AC16, measurement spec §4c
# Synthetic selection key and owner namespace: audit sessions are not real guests.
AUDIT_VARIETY_KEY = b"tarot-audit-synthetic-variety-key"
AUDIT_OWNERS = uuid.UUID("6f1c0b4e-7a1d-4c55-9e35-0b2d5c7a9e11")
_TRAILING = re.compile(r"[\s.!?…,;:]+$")


def _normalize(text: str) -> str:
    """Measurement spec §4c normalisation (same as scripts/variety_baseline.normalize)."""

    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return _TRAILING.sub("", folded)


def _audit_owner(item_id: str) -> uuid.UUID:
    return uuid.uuid5(AUDIT_OWNERS, item_id)


def audit_stance_and_headlines() -> tuple[list[str], dict[str, Any]]:
    """B2-3/B2-4 on the bank (US-20 AC20): stance distribution, opening (headline + summary)
    duplicates per voice (< 10%; headline-only duplicates reported), no generic copy. B2-4b
    adds, on the same readings, the provenance trace of every provider payload (US-20 AC06,
    direct voices; Roast is never sent) and the machine items of the psychology checklist
    (US-20 AC14).

    Every accepted bank question x every spread map x all four voices, with cards drawn from a
    seed fixed per question and the variants a synthetic guest's first session would get. Roast
    on a sensitive question renders in the default voice and is counted there.
    """

    import random

    from app.domains.content_rewrite.models import RewriteSurface
    from app.domains.tarot import checklist, provenance
    from app.domains.tarot import roles as tarot_roles
    from app.domains.tarot.meaning_brief import BRIEF_LIMITS
    from app.domains.tarot.variants import choose_variants
    from app.infrastructure.generation.privacy import TAROT_FOCUS_SENTENCES, PrivacyMinimiser

    engine = TarotReadingEngine()
    items: list[dict[str, Any]] = json.loads(QUESTION_BANK.read_text())["items"]
    traced = 0
    negative_by_map: dict[str, Counter[int]] = defaultdict(Counter)
    scenes_with_advice = triggers = steps = 0
    cards = [card.id for card in all_cards()]
    headlines: dict[TarotVoice, list[str]] = {voice: [] for voice in TarotVoice}
    openings: dict[TarotVoice, list[str]] = {voice: [] for voice in TarotVoice}
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
            variants = choose_variants(
                AUDIT_VARIETY_KEY,
                _audit_owner(item["id"]),
                0,
                tuple(key for key, _ in engine.positions_for(spread_map)),
            )
            for voice in TarotVoice:
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
                        variants=variants,
                    )
                except TarotContentRejected as exc:
                    failures.append(f"stance/{item['id']}/{spread_map.value}/{voice.value}: {exc}")
                    continue
                # Measurement spec §4c T2: normalised, per (effective) voice.
                headlines[reading.voice].append(
                    " ".join(reading.headline.casefold().split()).rstrip(".!?")
                )
                openings[reading.voice].append(
                    " ".join(f"{reading.headline} {reading.summary}".casefold().split())
                )
                levels[reading.stance.level.value if reading.stance else "none"] += 1
                prose = " ".join(
                    [reading.headline, reading.summary]
                    + [p.meaning_here + " " + (p.small_action or "") for p in reading.positions]
                ).casefold()
                generic += any(prefix in prose for prefix in tarot_roles.RETIRED_PREFIXES)
                label = f"{item['id']}/{spread_map.value}/{voice.value}"
                result = checklist.check(reading)
                if not result.gated_ok:
                    failures.append(f"checklist/{label}: {result}")
                negative_by_map[spread_map.value][result.negative_ideas] += 1
                scenes_with_advice += result.scenes_with_advice_words
                triggers += result.step_action_has_trigger
                steps += 1
                if reading.voice is TarotVoice.ROAST:
                    continue
                brief = provenance.framed_brief(reading)
                positions = provenance.framed_positions(reading)
                if brief is None or positions is None:
                    failures.append(f"provenance/{label}: no catalog resolution")
                    continue
                payload = {
                    "category": "general",
                    "focus_key": "clarity",
                    "focus_sentence": TAROT_FOCUS_SENTENCES["clarity"],
                    "meaning_brief": brief,
                    "positions": positions,
                }
                # The normalized form is what the queue and the provider adapter emit.
                normalized = PrivacyMinimiser().minimise(RewriteSurface.TAROT, payload)
                untraced = [
                    path
                    for candidate in (payload, normalized)
                    for path in provenance.untraced_paths(
                        candidate,
                        focus_sentences=TAROT_FOCUS_SENTENCES,
                        limits=frozenset(BRIEF_LIMITS),
                    )
                ]
                if untraced:
                    failures.append(f"provenance/{label}: untraced {untraced[:3]}")
                    continue
                traced += 1
    rates = {
        voice.value: round(1 - len(set(values)) / len(values), 4) if values else 0.0
        for voice, values in headlines.items()
    }
    opening_rates = {
        voice.value: round(1 - len(set(values)) / len(values), 4) if values else 0.0
        for voice, values in openings.items()
    }
    if max(opening_rates.values()) >= OPENING_DUPLICATE_CEILING:
        failures.append(f"opening duplicate rate {opening_rates} >= 0.10")
    if generic:
        failures.append(f"{generic} framed readings still carry generic filler")
    metrics = {
        "readings": sum(len(values) for values in headlines.values()),
        "headline_duplicate_rate": rates,
        "opening_duplicate_rate": opening_rates,
        "stance_levels": dict(sorted(levels.items())),
        "generic": generic,
        "provenance_traced": traced,
        "negative_ideas_by_map": {
            name: dict(sorted(counts.items())) for name, counts in sorted(negative_by_map.items())
        },
        "scenes_with_advice_words": scenes_with_advice,
        "step_actions_with_trigger": f"{triggers}/{steps}",
    }
    return failures, metrics


def audit_t4() -> tuple[list[str], dict[str, Any]]:
    """T4 (US-20 AC16, measurement spec §4c): same card x role x topic, every pair of different
    bank questions in the topic, share of pairs whose role sentence differs after normalising.

    Every accepted bank question x every map x every position x all 78 cards, in the default
    voice (playful_grounded, as P1). Three ways to assign session variants:

    * ``per_session``: each question is the first session of its own synthetic guest (gate);
    * ``question_only``: every variant index 0, so only the question changes the text (gate,
      proves the text follows the question and not only the salt);
    * ``same_guest``: one synthetic guest asks the topic's questions in a row (information).

    The sentence comes from ``roles.meaning_for``, the function the renderer uses; a sample of
    full renders must match it exactly.
    """

    from app.domains.tarot import roles as tarot_roles
    from app.domains.tarot.engine import _CardMeaning, _resource_step, _tension_parts
    from app.domains.tarot.variants import DEFAULT_VARIANTS, TarotVariants, choose_variants

    engine = TarotReadingEngine()
    items: list[dict[str, Any]] = json.loads(QUESTION_BANK.read_text())["items"]
    cards = all_cards()
    by_topic: dict[TarotContext, dict[str, Any]] = defaultdict(dict)
    item_ids: dict[str, str] = {}
    for item in items:
        if not item["expected"]["accepted"]:
            continue
        context = TarotContext(item["context"])
        assessment = engine.assess_question(item["question"], context)
        if assessment.accepted and assessment.frame is not None:
            by_topic[context][item["question"]] = assessment.frame
            item_ids[item["question"]] = item["id"]
    fields = {
        (card.id, context): (
            meaning.core,
            _tension_parts(meaning.tension)[0],
            _resource_step(meaning.resource),
        )
        for card in cards
        for context in TarotContext
        for meaning in (_CardMeaning.for_context(card, context),)
    }
    same_guest = uuid.uuid5(AUDIT_OWNERS, "same-guest")

    def variants_for(mode: str, question: str, index: int, keys: tuple[str, ...]) -> TarotVariants:
        if mode == "question_only":
            return DEFAULT_VARIANTS
        if mode == "same_guest":
            return choose_variants(AUDIT_VARIETY_KEY, same_guest, index, keys)
        return choose_variants(AUDIT_VARIETY_KEY, _audit_owner(item_ids[question]), 0, keys)

    def sentence(
        key: str, index: int, card_id: str, topic: TarotContext, frame: Any, chosen: TarotVariants
    ) -> str:
        core, tension, resource = fields[(card_id, topic)]
        return tarot_roles.meaning_for(
            key,
            core=core,
            tension=tension,
            resource=resource,
            frame=chosen.frame(key),
            lead=tarot_roles.lead_for(frame.form, chosen.lead, index),
        )

    failures: list[str] = []
    # Sample check: the measured sentence is the rendered one.
    spread = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
    for topic, questions in by_topic.items():
        question, frame = next(iter(questions.items()))
        for spread_map in TarotSpreadMap:
            keys = tuple(key for key, _ in engine.positions_for(spread_map))
            chosen = variants_for("per_session", question, 0, keys)
            ids = tuple(card.id for card in cards[: len(keys)])
            reading = engine.render(
                card_ids=ids,
                spread=spread[len(keys)],
                spread_map=spread_map,
                context=topic,
                question=question,
                voice=TarotVoice.PLAYFUL_GROUNDED,
                frame=frame,
                variants=chosen,
            )
            for index, (key, card_id) in enumerate(zip(keys, ids, strict=True)):
                if reading.positions[index].meaning_here != sentence(
                    key, index, card_id, topic, frame, chosen
                ):
                    failures.append(f"t4/sample/{topic.value}/{spread_map.value}/{key}")

    metrics: dict[str, Any] = {}
    for mode in ("per_session", "question_only", "same_guest"):
        total = same = 0
        for spread_map in TarotSpreadMap:
            keys = tuple(key for key, _ in engine.positions_for(spread_map))
            for topic, questions in by_topic.items():
                by_question = {
                    question: variants_for(mode, question, order, keys)
                    for order, question in enumerate(questions)
                }
                n = len(questions)
                for index, key in enumerate(keys):
                    for card in cards:
                        counts = Counter(
                            _normalize(sentence(key, index, card.id, topic, frame, by_question[q]))
                            for q, frame in questions.items()
                        )
                        total += comb(n, 2)
                        same += sum(comb(k, 2) for k in counts.values())
        metrics[mode] = {
            "question_pairs": total,
            "different": total - same,
            "rate": round((total - same) / total, 4) if total else 0.0,
        }
    for mode in ("per_session", "question_only"):
        if metrics[mode]["rate"] < T4_FLOOR:
            failures.append(f"T4 {mode} {metrics[mode]['rate']} < {T4_FLOOR}")
    metrics["questions"] = sum(len(q) for q in by_topic.values())
    return failures, metrics


LONG_QUESTIONS = (
    "Khi nào mình nên chọn ở lại để nhận thêm việc?",  # timing: the readiness line is reserved
    "Mình có nên nhận thêm việc ở chỗ làm không?",  # yes/no: a stance and its reasons
)


def audit_worst_length() -> tuple[list[str], int]:
    """Longest unique-card draws per map x context x voice must still fit every budget (B2-3).

    For each position, the unused card whose role field is longest in that context is drawn
    (option roles count core + tension), then the reading is rendered for a timing and a
    yes/no question. Any rejection (budget, density, links) fails the audit.
    """

    from app.domains.tarot import roles as tarot_roles
    from app.domains.tarot.engine import _CardMeaning, _resource_step, _tension_parts
    from app.domains.tarot.variants import TarotVariants

    engine = TarotReadingEngine()
    cards = all_cards()
    failures: list[str] = []
    rendered = 0
    spread = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}

    def length(card_id: str, key: str, context: TarotContext) -> int:
        meaning = _CardMeaning.for_context(next(c for c in cards if c.id == card_id), context)
        field = tarot_roles.ROLES[key].field
        core, tension = meaning.core, _tension_parts(meaning.tension)[0]
        resource = _resource_step(meaning.resource)
        text = {
            tarot_roles.RoleField.CORE: core,
            tarot_roles.RoleField.TENSION: tension,
            tarot_roles.RoleField.RESOURCE: resource,
            tarot_roles.RoleField.OPTION: f"{core} {tension}",
        }[field]
        return len(text.split())

    for spread_map in TarotSpreadMap:
        keys = [key for key, _ in engine.positions_for(spread_map)]
        for context in TarotContext:
            used: list[str] = []
            for key in keys:
                candidates = [c.id for c in cards if c.id not in used]
                pick = max(candidates, key=lambda c: (length(c, key, context), c))
                used.append(pick)
            for question in LONG_QUESTIONS:
                assessment = engine.assess_question(question, context)
                for voice in TarotVoice:
                    # B2-4: every frame, lead and headline index (frames are density-checked
                    # exhaustively in tests/tarot/test_variants.py).
                    for index in range(tarot_roles.FRAME_VARIANTS):
                        variants = TarotVariants(
                            key_version=1,
                            lead=index,
                            headline=index,
                            frames=dict.fromkeys(keys, index),
                        )
                        rendered += 1
                        try:
                            engine.render(
                                card_ids=tuple(used),
                                spread=spread[len(keys)],
                                spread_map=spread_map,
                                context=context,
                                question=question,
                                voice=voice,
                                question_intent=assessment.intent,
                                frame=assessment.frame,
                                variants=variants,
                            )
                        except TarotContentRejected as exc:
                            failures.append(
                                f"worst-length/{spread_map.value}/{context.value}/"
                                f"{voice.value}/{index}: {exc}"
                            )
    return failures, rendered


def main() -> None:
    failures = audit()
    worst_failures, worst_count = audit_worst_length()
    failures += worst_failures
    stance_failures, stance_metrics = audit_stance_and_headlines()
    failures += stance_failures
    t4_failures, t4 = audit_t4()
    failures += t4_failures
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
    print(f"Worst-length draws (B2-3/B2-4): {worst_count} renders within every budget.")
    print(
        f"Stance and headlines (B2-3/B2-4): {stance_metrics['readings']} framed readings "
        f"(bank x {len(TarotSpreadMap)} maps x {len(TarotVoice)} voices); opening duplicate rate "
        f"{stance_metrics['opening_duplicate_rate']} (headline only, reported: "
        f"{stance_metrics['headline_duplicate_rate']}); stance levels "
        f"{stance_metrics['stance_levels']}; generic filler {stance_metrics['generic']}."
    )
    print(
        f"Provenance (B2-4b, AC06): {stance_metrics['provenance_traced']} direct-voice provider "
        "payloads, built and minimised forms, every string traced to a closed label or a catalog "
        "code."
    )
    print(
        "Psychology checklist (B2-4b, AC14): gated items pass on every reading (headline gives "
        "no advice, no coercion, ends on the step, summary ends on the step). For the owner: "
        f"pitfall/cost ideas per map {stance_metrics['negative_ideas_by_map']}; scene slots with "
        f"advice words {stance_metrics['scenes_with_advice_words']}; step actions with a 'khi' "
        f"trigger {stance_metrics['step_actions_with_trigger']}."
    )
    print(
        f"T4 same card x role x topic (B2-4, floor {T4_FLOOR}): per session "
        f"{t4['per_session']['rate']} of {t4['per_session']['question_pairs']} pairs; question "
        f"only {t4['question_only']['rate']}; same guest in a row {t4['same_guest']['rate']} "
        f"({t4['questions']} bank questions)."
    )


if __name__ == "__main__":
    main()
