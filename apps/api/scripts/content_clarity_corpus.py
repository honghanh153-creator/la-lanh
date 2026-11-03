"""Synthetic, deterministic readings for the content clarity ratchet (spec A12).

Every surface is rendered the way production renders it, from synthetic charts and questions
only: Daily (direct and roast), Tarot through the session intake path (question assessment,
spread map, effective voice, stored variants) in both production voices, Radar in all four
contexts and all relationship voices, and the Khám phá overview tiles (Western and Jyotish).
Only the body text a user reads is kept; evidence, receipts, factor codes and UI labels are not.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.domains.astro.engine import NatalChartEngine
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    ZodiacSign,
)
from app.domains.radar.reading import CONTEXTS as RADAR_CONTEXTS
from app.domains.radar.reading import build_radar_reading
from app.domains.readings.clarity_lint import ClarityDocument
from app.domains.readings.models import BackgroundLens, ReadingPlan, ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.service import InsightReadingService
from app.domains.readings.voice import DailySections, roast_daily_sections
from app.domains.relationships.models import RelationshipVoice
from app.domains.tarot.engine import TarotContentRejected, TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import TarotContext, TarotReading, TarotSpread, TarotVoice
from app.domains.tarot.variants import choose_variants
from app.domains.tarot.voice import effective_voice

# A12 minimums from the spec; the committed baseline may only raise them.
MINIMUM_SAMPLES = {"daily": 60, "tarot": 200, "radar": 80, "kham_pha": 80}
DAILY_COUNT = 64
TAROT_COUNT = 240
RADAR_COUNT = 96
KHAM_PHA_COUNT = 88

_SEED = 20261101
# A fixed, non-secret key so stored Tarot variants are exercised deterministically.
_TAROT_VARIETY_KEY = b"content-clarity-synthetic-variety-key"
_LENSES = tuple(lens for lens in BackgroundLens if lens is not BackgroundLens.AUTO)
_SPREAD_CARDS = {TarotSpread.ONE_CARD: 1, TarotSpread.THREE_CARD: 3, TarotSpread.FIVE_CARD: 5}
_TAROT_QUESTIONS: dict[TarotContext, tuple[str, ...]] = {
    TarotContext.GENERAL: (
        "Điều gì đang làm mình chần chừ với kế hoạch học thêm?",
        "Mình có nên bắt đầu lại thói quen chạy bộ buổi sáng không?",
        "Mình cần nhìn rõ điều gì trước khi đổi chỗ ở?",
    ),
    TarotContext.RELATIONSHIPS: (
        "Mình cần nhìn rõ điều gì trước khi nói chuyện tiếp với bạn ấy?",
        "Mình có nên rủ bạn ấy đi xem phim cuối tuần này không?",
        "Mình cần đặt ranh giới nào trong mối quan hệ này?",
    ),
    TarotContext.WORK: (
        "Mình có nên nhận thêm dự án mới tháng này không?",
        "Mình nên nói gì để cuộc họp nhóm tuần này rõ hơn?",
        "Mình cần bỏ bớt việc gì để kịp hạn nộp báo cáo?",
    ),
    TarotContext.COMMUNICATION: (
        "Mình nên mở lời với sếp về lịch làm thế nào?",
        "Câu nào mình cần nói thẳng thay vì giải thích vòng?",
        "Mình nên trả lời tin nhắn của nhóm bạn thế nào cho nhẹ?",
    ),
    TarotContext.ENERGY: (
        "Mình cần làm gì để đỡ uể oải vào buổi chiều?",
        "Việc nào đang lấy nhiều sức của mình nhất tuần này?",
        "Mình nên sắp xếp lại buổi tối thế nào để ngủ sớm hơn?",
    ),
    TarotContext.SELF_CARE: (
        "Tuần này mình cần bớt việc gì để đỡ mệt?",
        "Mình đang né gọi tên nhu cầu nào của bản thân?",
        "Mình có thể chăm phần đang quá tải bằng cách nào?",
    ),
}


def date_only_chart(sign: ZodiacSign) -> DateOnlySunResult:
    return DateOnlySunResult(
        status="certain",
        sign=sign,
        candidates=(sign,),
        provenance=EngineProvenance(version="synthetic", profile="content-review"),
    )


def daily_review_plan(
    planner: ReadingPlanner,
    engine: NatalChartEngine,
    chart: NatalChart | DateOnlySunResult,
    lens: BackgroundLens,
    start: date,
    index: int,
) -> ReadingPlan:
    """Exact charts are reviewed on their first day (within 30) that has a real
    "Vì sao hôm nay?" reason, so that sentence is read too; others on the base day."""

    base = start + timedelta(days=index)
    if not isinstance(chart, NatalChart):
        return planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            background_lens=lens,
            editorial_seed=base.isoformat(),
        )
    first: ReadingPlan | None = None
    for offset in range(30):
        day = base + timedelta(days=offset)
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            transits=engine.calculate_transit_to_natal(
                chart, datetime(day.year, day.month, day.day, 5, tzinfo=UTC)
            ),
            background_lens=lens,
            editorial_seed=day.isoformat(),
        )
        first = first or plan
        if plan.daily_selection is not None and plan.daily_selection.transit_ref is not None:
            return plan
    if first is None:  # pragma: no cover - range(30) always yields a plan
        raise RuntimeError("no Daily review plan")
    return first


def synthetic_chart_input(rng: random.Random) -> ChartInput:
    """A random birth moment in 1975-2006 at a random point inside Vietnam's bounding box."""

    moment = datetime(1975, 1, 1, tzinfo=UTC) + timedelta(minutes=rng.randrange(32 * 365 * 24 * 60))
    return ChartInput(
        utc_datetime=moment,
        latitude=round(rng.uniform(8.6, 23.3), 4),
        longitude=round(rng.uniform(102.2, 109.4), 4),
    )


def _chart(
    engine: NatalChartEngine,
    rng: random.Random,
    config: CalculationConfig | None = None,
) -> NatalChart:
    return engine.calculate_chart(
        synthetic_chart_input(rng), config or CalculationConfig.western_recommended()
    )


def daily_documents(count: int = DAILY_COUNT) -> tuple[ClarityDocument, ...]:
    rng = random.Random(f"{_SEED}:daily")  # noqa: S311 - synthetic fixtures
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    engine = NatalChartEngine()
    signs = tuple(ZodiacSign)
    documents: list[ClarityDocument] = []
    for index in range(count):
        chart: NatalChart | DateOnlySunResult = (
            date_only_chart(signs[index % len(signs)]) if index % 2 == 0 else _chart(engine, rng)
        )
        plan = daily_review_plan(
            planner, engine, chart, _LENSES[index % len(_LENSES)], date(2026, 10, 1), index
        )
        candidate = renderer.render(plan)
        sections = DailySections(
            candidate.hook, candidate.thesis, candidate.manifestation, candidate.micro_action
        )
        roast = index % 4 in {1, 2}
        if roast:
            sections = roast_daily_sections(sections)
        documents.append(
            ClarityDocument(
                surface="daily",
                sample_id=f"daily-{index:03d}",
                variant="roast" if roast else "direct",
                sections=(
                    ("hook", sections.hook),
                    ("thesis", sections.thesis),
                    ("scene", sections.manifestation),
                    ("action", sections.micro_action),
                    *((("why_today", candidate.transit),) if candidate.transit else ()),
                ),
            )
        )
    return tuple(documents)


# Every text field of a Tarot reading, by model, with what the corpus does with it. A field the
# Tarot page shows must be linted or named here with the reason it is not (tested against
# apps/web/src/features/tarot/TarotPage.tsx), so new visible copy cannot skip the ratchet.
TAROT_LINTED_FIELDS: dict[str, frozenset[str]] = {
    "TarotReading": frozenset({"headline", "summary", "closing_prompt"}),
    "TarotStance": frozenset({"conclusion"}),
    "TarotStanceReason": frozenset({"text"}),
    "TarotReadingPosition": frozenset(
        {"meaning_here", "everyday_scene", "reflection_question", "small_action"}
    ),
}
TAROT_UNLINTED_FIELDS: dict[str, dict[str, str]] = {
    "TarotReading": {
        "question": "the reader's own words, echoed back; not copy the engine writes",
        "disclaimer": "one fixed engine string on every reading, reviewed in code, not generated",
    },
    "TarotReadingPosition": {
        "key": "identifier",
        "label": "spread position label from the fixed spread map (UI chrome)",
    },
    "TarotStanceReason": {
        "position_key": "identifier",
        "card_id": "identifier",
    },
    "TarotStance": {"version": "identifier"},
}


def tarot_sections(reading: TarotReading) -> tuple[tuple[str, str], ...]:
    sections: list[tuple[str, str]] = [("headline", reading.headline), ("summary", reading.summary)]
    if reading.stance is not None:
        sections.append(("stance", reading.stance.conclusion))
        sections.extend(
            (f"stance_reason_{reason.position_key}", reason.text)
            for reason in reading.stance.reasons
        )
    for position in reading.positions:
        sections.extend(
            (
                (f"meaning_{position.key}", position.meaning_here),
                (f"scene_{position.key}", position.everyday_scene),
                (f"reflection_{position.key}", position.reflection_question),
            )
        )
        if position.small_action:
            sections.append((f"action_{position.key}", position.small_action))
    sections.append(("closing", reading.closing_prompt))
    return tuple(sections)


def tarot_readings(count: int = TAROT_COUNT) -> Iterator[tuple[int, TarotReading]]:
    """Mirrors ``TarotSessionService.start`` + ``select``; content rejections are skipped like
    production skips publishing them, so coverage is checked on rendered readings only."""

    rng = random.Random(f"{_SEED}:tarot")  # noqa: S311 - synthetic fixtures
    engine = TarotReadingEngine()
    card_ids = tuple(card.id for card in all_cards())
    contexts = tuple(_TAROT_QUESTIONS)
    spreads = tuple(_SPREAD_CARDS)
    for index in range(count):
        spread = spreads[index % len(spreads)]
        requested = TarotVoice.PLAYFUL_GROUNDED if (index // 3) % 2 == 0 else TarotVoice.ROAST
        context = contexts[(index // 6) % len(contexts)]
        pool = _TAROT_QUESTIONS[context]
        question = pool[(index // 36) % len(pool)]
        assessment = engine.assess_question(question, context)
        if not assessment.accepted or assessment.intent is None:
            raise RuntimeError(f"synthetic Tarot question was not accepted: {question}")
        spread_map = engine.choose_spread_map(
            spread, assessment.intent, assessment.normalized_question
        )
        voice = effective_voice(requested, assessment.normalized_question)
        variants = choose_variants(
            _TAROT_VARIETY_KEY,
            uuid5(NAMESPACE_URL, f"la-lanh:content-clarity:tarot:{index // 12}"),
            index % 12,
            tuple(key for key, _ in engine.positions_for(spread_map)),
        )
        try:
            reading = engine.render(
                card_ids=tuple(rng.sample(card_ids, _SPREAD_CARDS[spread])),
                spread=spread,
                spread_map=spread_map,
                context=context,
                question=assessment.normalized_question,
                voice=voice,
                question_intent=assessment.intent,
                frame=assessment.frame,
                variants=variants,
            )
        except TarotContentRejected:
            continue
        yield index, reading


def tarot_documents(count: int = TAROT_COUNT) -> tuple[ClarityDocument, ...]:
    return tuple(
        ClarityDocument(
            surface="tarot",
            sample_id=f"tarot-{index:03d}",
            variant=reading.voice.value,
            sections=tarot_sections(reading),
        )
        for index, reading in tarot_readings(count)
    )


def _texts(items: Any, *keys: str) -> Iterator[str]:
    for item in items or ():
        for key in keys:
            value = item.get(key) if isinstance(item, dict) else None
            if isinstance(value, str) and value.strip():
                yield value


def radar_sections(reading: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """Body text of a Radar result. The ``why`` factors and every evidence ``plain`` line are
    the evidence layer; labels, kickers and level labels are UI chrome."""

    sections: list[tuple[str, str]] = [
        ("headline", reading["headline"]),
        ("summary", reading["summary"]),
    ]
    signature = reading.get("pair_signature") or {}
    sections.extend(("area", note) for note in _texts(signature.get("areas"), "note"))
    sections.extend(
        ("map", text) for text in _texts(reading.get("compatibility_map"), "title", "body")
    )
    for section in reading["sections"]:
        key = section["key"]
        if section.get("body"):
            sections.append((f"{key}_body", section["body"]))
        if section.get("question"):
            sections.append((f"{key}_question", section["question"]))
        scene = section.get("scene")
        if isinstance(scene, dict) and scene.get("body"):
            sections.append((f"scene_{key}", scene["body"]))
        observation = section.get("observation")
        if isinstance(observation, str) and observation.strip():
            sections.append((f"{key}_observation", observation))
        elif isinstance(observation, dict):
            sections.extend(
                (f"{key}_observation", text) for text in _texts([observation], "title", "body")
            )
        sections.extend(
            (f"{key}_highlight", text)
            for text in _texts(section.get("highlights"), "title", "body")
        )
        sections.extend(
            (f"{key}_perspective", text)
            for text in _texts(section.get("perspectives"), "title", "body")
        )
    return tuple(sections)


def radar_documents(count: int = RADAR_COUNT) -> tuple[ClarityDocument, ...]:
    rng = random.Random(f"{_SEED}:radar")  # noqa: S311 - synthetic fixtures
    engine = NatalChartEngine()
    voices = tuple(RelationshipVoice)
    documents: list[ClarityDocument] = []
    for index in range(count):
        context = RADAR_CONTEXTS[index % len(RADAR_CONTEXTS)]
        voice = voices[(index // len(RADAR_CONTEXTS)) % len(voices)]
        bundle = engine.calculate_relationship_bundle(_chart(engine, rng), _chart(engine, rng))
        reading = build_radar_reading(bundle, context=context, voice=voice)
        documents.append(
            ClarityDocument(
                surface="radar",
                sample_id=f"radar-{index:03d}",
                variant=context,
                sections=radar_sections(reading),
            )
        )
    return tuple(documents)


def kham_pha_documents(count: int = KHAM_PHA_COUNT) -> tuple[ClarityDocument, ...]:
    """Khám phá overview tiles; one in four charts uses the Jyotish config the route offers."""

    rng = random.Random(f"{_SEED}:kham-pha")  # noqa: S311 - synthetic fixtures
    engine = NatalChartEngine()
    service = InsightReadingService()
    observed_at = datetime(2026, 11, 1, 5, tzinfo=UTC)
    documents: list[ClarityDocument] = []
    for index in range(count):
        config = (
            CalculationConfig.jyotish_recommended()
            if index % 4 == 3
            else CalculationConfig.western_recommended()
        )
        reading = service.overview(_chart(engine, rng, config), observed_at=observed_at)
        sections = tuple(
            (f"{field}_{claim.id}", text)
            for claim in reading.claims
            for field, text in (
                ("title", claim.title),
                ("summary", claim.summary),
                ("hook", claim.hook),
                ("meaning", claim.meaning),
                ("scene", claim.manifestation),
                ("watch", claim.watch_for),
                ("action", claim.micro_action),
            )
            if text.strip()
        )
        documents.append(
            ClarityDocument(
                surface="kham_pha",
                sample_id=f"kham-pha-{index:03d}",
                variant=config.tradition.value,
                sections=sections,
            )
        )
    return tuple(documents)


SURFACE_BUILDERS: dict[str, Callable[[], tuple[ClarityDocument, ...]]] = {
    "daily": daily_documents,
    "tarot": tarot_documents,
    "radar": radar_documents,
    "kham_pha": kham_pha_documents,
}


def build_clarity_corpus() -> dict[str, tuple[ClarityDocument, ...]]:
    return {surface: build() for surface, build in SURFACE_BUILDERS.items()}
