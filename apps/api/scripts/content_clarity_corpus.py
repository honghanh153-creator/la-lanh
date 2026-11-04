"""Synthetic, deterministic readings for the content clarity ratchet (spec A12).

Every surface is rendered the way production renders it, from synthetic charts and questions
only: Daily (direct and roast), Tarot through the session intake path (question assessment,
spread map, effective voice, stored variants) in both production voices, Radar in all four
contexts and all relationship voices, and the Khám phá overview tiles (Western and Jyotish).
Only the body text a user reads is kept; evidence, receipts, factor codes and UI labels are not.
Each reading also names its first screen (A9) and carries the engine's facts for it (A15); Daily
adds 30-day runs for the personas with a birth time (A13).
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.domains.astro.engine import NatalChartEngine, house_for_longitude
from app.domains.astro.models import (
    CalculationConfig,
    ChartInput,
    DateOnlySunResult,
    EngineProvenance,
    NatalChart,
    TransitToNatalSnapshot,
    ZodiacSign,
)
from app.domains.radar.reading import CONTEXTS as RADAR_CONTEXTS
from app.domains.radar.reading import build_radar_reading
from app.domains.readings.clarity_lint import (
    DAILY_FOLLOW_DAYS,
    AstroFacts,
    ClarityDocument,
    DailyDay,
    first_screen_limit,
)
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
DAILY_FOLLOW_START = date(2026, 10, 1)

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

    return daily_review_day(planner, engine, chart, lens, start, index)[0]


def daily_plan_for(
    planner: ReadingPlanner,
    engine: NatalChartEngine,
    chart: NatalChart,
    lens: BackgroundLens,
    day: date,
) -> tuple[ReadingPlan, TransitToNatalSnapshot]:
    transits = engine.calculate_transit_to_natal(
        chart, datetime(day.year, day.month, day.day, 5, tzinfo=UTC)
    )
    plan = planner.plan(
        chart,
        purpose=ReadingPurpose.DAILY_NOTE,
        transits=transits,
        background_lens=lens,
        editorial_seed=day.isoformat(),
    )
    return plan, transits


def daily_review_day(
    planner: ReadingPlanner,
    engine: NatalChartEngine,
    chart: NatalChart | DateOnlySunResult,
    lens: BackgroundLens,
    start: date,
    index: int,
) -> tuple[ReadingPlan, TransitToNatalSnapshot | None]:
    """``daily_review_plan`` with the transit snapshot the plan was made from."""

    base = start + timedelta(days=index)
    if not isinstance(chart, NatalChart):
        plan = planner.plan(
            chart,
            purpose=ReadingPurpose.DAILY_NOTE,
            background_lens=lens,
            editorial_seed=base.isoformat(),
        )
        return plan, None
    first: tuple[ReadingPlan, TransitToNatalSnapshot] | None = None
    for offset in range(30):
        plan, transits = daily_plan_for(planner, engine, chart, lens, base + timedelta(days=offset))
        first = first or (plan, transits)
        if plan.daily_selection is not None and plan.daily_selection.transit_ref is not None:
            return plan, transits
    if first is None:  # pragma: no cover - range(30) always yields a plan
        raise RuntimeError("no Daily review plan")
    return first


def chart_facts(
    chart: NatalChart | DateOnlySunResult, transits: TransitToNatalSnapshot | None = None
) -> AstroFacts:
    """A15 facts straight from the engine: natal placements, houses (from the cusps) and
    aspects, plus the transit contacts the reading was planned from."""

    if not isinstance(chart, NatalChart):
        return AstroFacts(
            placements=frozenset({("sun", chart.sign.value)} if chart.sign is not None else ())
        )
    placements = {(position.body.value, position.sign.value) for position in chart.bodies}
    houses: set[tuple[str, int]] = set()
    if chart.houses:
        placements.add(("ascendant", min(chart.houses, key=lambda house: house.number).sign.value))
        houses = {
            (position.body.value, house_for_longitude(position.longitude, chart.houses))
            for position in chart.bodies
        }
    contacts = {
        (first.value, second.value, aspect.kind, "approaching" if aspect.applying else "separating")
        for aspect in chart.aspects
        for first, second in ((aspect.body_a, aspect.body_b), (aspect.body_b, aspect.body_a))
    }
    for contact in transits.contacts if transits is not None else ():
        contacts.add(
            (
                contact.transit_body.value,
                contact.natal_body.value,
                contact.kind,
                contact.phase.value,
            )
        )
    return AstroFacts(frozenset(placements), frozenset(houses), frozenset(contacts))


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


def daily_charts(count: int = DAILY_COUNT) -> tuple[NatalChart | DateOnlySunResult, ...]:
    """Every other Daily persona has a birth date only; the rest have an exact chart."""

    rng = random.Random(f"{_SEED}:daily")  # noqa: S311 - synthetic fixtures
    engine = NatalChartEngine()
    signs = tuple(ZodiacSign)
    return tuple(
        date_only_chart(signs[index % len(signs)]) if index % 2 == 0 else _chart(engine, rng)
        for index in range(count)
    )


# A9: the Daily home card shows the hook, the scene (or the thesis when there is no scene) and
# the small action (apps/web/src/features/home/HomePage.tsx, HomeDailySignal).
def daily_first_screen(sections: DailySections) -> tuple[str, ...]:
    return ("hook", "scene" if sections.manifestation else "thesis", "action")


def daily_documents(count: int = DAILY_COUNT) -> tuple[ClarityDocument, ...]:
    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    engine = NatalChartEngine()
    documents: list[ClarityDocument] = []
    for index, chart in enumerate(daily_charts(count)):
        plan, transits = daily_review_day(
            planner, engine, chart, _LENSES[index % len(_LENSES)], DAILY_FOLLOW_START, index
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
                first_screen=daily_first_screen(sections),
                first_screen_limit=first_screen_limit("daily"),
                facts=chart_facts(chart, transits),
            )
        )
    return tuple(documents)


def _transit_body(ref: str) -> str:
    return ref.split(":")[1]


def _transit_reason(ref: str) -> str:
    """A transit's bodies and aspect, without the orb and phase that change every day."""

    return ":".join(ref.split(":")[:5])


def daily_days(count: int = DAILY_COUNT) -> tuple[DailyDay, ...]:
    """A13: 30 consecutive days for every Daily persona with a birth time, in the direct voice."""

    planner = ReadingPlanner()
    renderer = DeterministicVietnameseRenderer()
    engine = NatalChartEngine()
    days: list[DailyDay] = []
    for index, chart in enumerate(daily_charts(count)):
        if not isinstance(chart, NatalChart):
            continue
        for offset in range(DAILY_FOLLOW_DAYS):
            day = DAILY_FOLLOW_START + timedelta(days=offset)
            plan, _ = daily_plan_for(planner, engine, chart, _LENSES[index % len(_LENSES)], day)
            selection = plan.daily_selection
            ref = selection.transit_ref if selection is not None else None
            days.append(
                DailyDay(
                    persona=f"daily-{index:03d}",
                    day=day.isoformat(),
                    headline=renderer.render(plan).hook,
                    reason=(
                        _transit_reason(ref)
                        if ref is not None
                        else (selection.rule_key if selection is not None else "none")
                    ),
                    sky_bodies=(_transit_body(ref),) if ref is not None else (),
                )
            )
    return tuple(days)


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


def tarot_first_screen(sections: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    """A9: headline, stance, summary and closing are shown; each card's chapter is a closed
    ``<details>`` (apps/web/src/features/tarot/TarotPage.tsx)."""

    return tuple(
        name
        for name, _ in sections
        if name in {"headline", "summary", "stance", "closing"} or name.startswith("stance_reason_")
    )


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
    documents: list[ClarityDocument] = []
    for index, reading in tarot_readings(count):
        sections = tarot_sections(reading)
        documents.append(
            ClarityDocument(
                surface="tarot",
                sample_id=f"tarot-{index:03d}",
                variant=reading.voice.value,
                sections=sections,
                first_screen=tarot_first_screen(sections),
                first_screen_limit=first_screen_limit("tarot", cards=len(reading.positions)),
            )
        )
    return tuple(documents)


def _texts(items: Any, *keys: str) -> Iterator[str]:
    for item in items or ():
        for key in keys:
            value = item.get(key) if isinstance(item, dict) else None
            if isinstance(value, str) and value.strip():
                yield value


def radar_first_screen(reading: dict[str, Any]) -> tuple[str, ...]:
    """A9: the v2 result shows the signature (summary, headline), the area notes and every
    section not in the "more" layer; "Xem thêm" folds the rest, and the compatibility map is not
    shown (apps/web/src/features/radar/RadarContinuePage.tsx, RadarResultView)."""

    shown = ["headline", "summary", "area"]
    for section in reading["sections"]:
        if section.get("layer") != "more":
            shown.extend((f"{section['key']}_body", f"{section['key']}_question"))
    return tuple(shown)


# Every key of a Radar section and of the items inside it (highlights, perspectives, scene,
# observation), with what the corpus does with it. A key RadarContinuePage.tsx shows must be
# linted or named here with the reason it is not (tested against the page and against every
# section the corpus renders), so new visible copy cannot skip the ratchet.
RADAR_SECTION_LINTED_FIELDS = frozenset(
    {"title", "body", "question", "scene", "observation", "highlights", "perspectives"}
)
RADAR_SECTION_UNLINTED_FIELDS: dict[str, str] = {
    "key": "identifier",
    "layer": "identifier (main view or the Xem thêm layer)",
    "depth": "identifier (picks the dossier layout)",
    "label": "section heading from the fixed SECTION_LABELS map (UI chrome)",
    "topics": "theme name chips from the fixed theme label map (UI chrome)",
    "factors": "the evidence layer of the why section (Vì sao ra kết quả này?)",
    "evidence": "the evidence layer (receipts behind a disclosure)",
}
RADAR_ITEM_LINTED_FIELDS = frozenset({"title", "body"})
RADAR_ITEM_UNLINTED_FIELDS: dict[str, str] = {
    "key": "identifier",
    "label": "kicker from a fixed label map (UI chrome)",
    "concept_id": "identifier",
    "evidence_ids": "identifiers of the evidence layer",
}


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
        if section.get("title"):
            sections.append((f"{key}_title", section["title"]))
        if section.get("body"):
            sections.append((f"{key}_body", section["body"]))
        if section.get("question"):
            sections.append((f"{key}_question", section["question"]))
        scene = section.get("scene")
        if isinstance(scene, dict):
            if scene.get("title"):
                sections.append((f"scene_{key}_title", scene["title"]))
            if scene.get("body"):
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


def radar_readings(count: int = RADAR_COUNT) -> Iterator[tuple[int, str, dict[str, Any]]]:
    """Synthetic pairs in every Radar context and relationship voice: (index, context, result)."""

    rng = random.Random(f"{_SEED}:radar")  # noqa: S311 - synthetic fixtures
    engine = NatalChartEngine()
    voices = tuple(RelationshipVoice)
    for index in range(count):
        context = RADAR_CONTEXTS[index % len(RADAR_CONTEXTS)]
        voice = voices[(index // len(RADAR_CONTEXTS)) % len(voices)]
        bundle = engine.calculate_relationship_bundle(_chart(engine, rng), _chart(engine, rng))
        yield index, context, build_radar_reading(bundle, context=context, voice=voice)


def radar_documents(count: int = RADAR_COUNT) -> tuple[ClarityDocument, ...]:
    return tuple(
        ClarityDocument(
            surface="radar",
            sample_id=f"radar-{index:03d}",
            variant=context,
            sections=radar_sections(reading),
            first_screen=radar_first_screen(reading),
            first_screen_limit=first_screen_limit("radar"),
            # Radar body text names no placement yet, so it carries no facts: any placement
            # it starts to name fails A15 until the pair's facts are wired here.
            facts=AstroFacts(),
        )
        for index, context, reading in radar_readings(count)
    )


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
        chart = _chart(engine, rng, config)
        reading = service.overview(chart, observed_at=observed_at)
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
                # A9: the overview grid shows each tile's title and summary
                # (apps/web/src/features/insights/InsightsPage.tsx).
                first_screen=tuple(
                    name for name, _ in sections if name.startswith(("title_", "summary_"))
                ),
                first_screen_limit=first_screen_limit("kham_pha"),
                facts=chart_facts(chart),
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
