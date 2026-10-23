"""Luna sprint S4: Tarot joins the chart-free rewrite allowlist, with proof.

Tarot never reads a birth chart. The rewrite payload carries closed labels, catalog-traced card
meanings and a fixed focus sentence, never the free-text question (see tarot/rewrite.py). This test
pins that, then config allows a Tarot rollout; Radar stays refused until S5.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import (
    TarotContext,
    TarotOrigin,
    TarotSelectedCard,
    TarotSessionState,
    TarotSessionView,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)
from app.domains.tarot.rewrite import compile_tarot_rewrite_request

NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
ENGINE = TarotReadingEngine()
QUESTIONS = (
    ("Mình có nên xin lỗi sau lần nói chuyện vừa rồi không?", TarotContext.RELATIONSHIPS),
    ("Mình có nên nghỉ ngơi sau tuần làm việc này không?", TarotContext.SELF_CARE),
    ("Mình nên chuẩn bị gì trước khi xin góp ý về báo cáo?", TarotContext.WORK),
    ("Vì sao mình hay giữ trong lòng thay vì nói ra?", TarotContext.RELATIONSHIPS),
)
MAPS = {
    TarotSpreadMap.ONE_FOCUS: (TarotSpread.ONE_CARD, ("major-sun",)),
    TarotSpreadMap.THREE_UNBLOCK: (TarotSpread.THREE_CARD, ("major-moon", "cups-ace", "wands-3")),
}
# Chart facts: birth data, zodiac signs, houses and degrees. Tarot card titles such as "Mặt Trời"
# are card names, not chart facts.
CHART_FACTS = re.compile(
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:19|20)\d{2}\b|\d+\s*°|"
    r"giờ sinh|ngày sinh|nơi sinh|cung hoàng đạo|cung mọc|nhà thứ|"
    r"bạch dương|kim ngưu|song tử|cự giải|sư tử|xử nữ|thiên bình|bọ cạp|nhân mã|ma kết|"
    r"bảo bình|song ngư|aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|"
    r"capricorn|aquarius|pisces|ascendant|natal|birth|latitude|longitude",
    re.IGNORECASE,
)


def _session(
    question: str, context: TarotContext, spread_map: TarotSpreadMap, voice: TarotVoice
) -> TarotSessionView:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted, question
    spread, cards = MAPS[spread_map]
    reading = ENGINE.render(
        card_ids=cards, spread=spread, spread_map=spread_map, context=context, question=question,
        voice=voice, question_intent=assessment.intent, frame=assessment.frame,
    )  # fmt: skip
    selected = tuple(
        TarotSelectedCard(fan_index=i, position_key=p.key, position_label=p.label, card=p.card)
        for i, p in enumerate(reading.positions)
    )
    return TarotSessionView(
        id=UUID("70000000-0000-4000-8000-000000000702"), version=4,
        state=TarotSessionState.COMPLETE, context=context, spread=spread, spread_map=spread_map,
        voice=voice, origin=TarotOrigin.DIRECT, question=question, required_cards=len(cards),
        selected_cards=selected, reading=reading, created_at=NOW, updated_at=NOW,
        expires_at=NOW + timedelta(days=29),
    )  # fmt: skip


@pytest.mark.parametrize(("question", "context"), QUESTIONS)
@pytest.mark.parametrize("spread_map", list(MAPS))
@pytest.mark.parametrize("voice", [v for v in TarotVoice if v is not TarotVoice.ROAST])
def test_tarot_payload_has_no_chart_fact_and_no_raw_question(
    question: str, context: TarotContext, spread_map: TarotSpreadMap, voice: TarotVoice
) -> None:
    request = compile_tarot_rewrite_request(
        uuid4(), _session(question, context, spread_map, voice),
        model_version="gpt-6-luna", prompt_version="test",
    )  # fmt: skip
    assert request is not None
    serialized = json.dumps(request.safe_payload, ensure_ascii=False)
    assert question not in serialized
    assert CHART_FACTS.search(serialized) is None, CHART_FACTS.search(serialized)
    assert set(request.safe_payload) == {
        "category", "focus_key", "focus_sentence", "meaning_brief", "positions",
    }  # fmt: skip


def _generation(rollout: dict[str, str]) -> Settings:
    return Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        generation_enabled=True,
        generation_provider="openai",
        generation_governance_approved=True,
        generation_surface_rollout=rollout,
    )


def test_config_allows_a_tarot_rollout_and_still_refuses_radar() -> None:
    assert (
        _generation({"daily_home": "full", "tarot": "beta_10"}).generation_surface_rollout["tarot"]
        == "beta_10"
    )
    with pytest.raises(ValueError, match="chart-free"):
        _generation({"daily_home": "full", "radar": "full"})
