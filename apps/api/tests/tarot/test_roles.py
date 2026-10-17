"""B2-2: role-based Tarot meaning and filler cleanup (US-20 AC07, AC12, AC13).

Task: docs/plans/2026-10-17-b2-2-tarot-roles-task.md.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, cast

import pytest

from app.domains.readings.review_agent import ContentReviewAgent, ReviewSample
from app.domains.tarot import roles
from app.domains.tarot.engine import (
    _POSITIONS,
    TarotContentRejected,
    TarotReadingEngine,
    _CardMeaning,
)
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import (
    TarotContext,
    TarotReading,
    TarotSpread,
    TarotSpreadMap,
    TarotVoice,
)

ENGINE = TarotReadingEngine()
CARDS = [card.id for card in all_cards()]
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
QUESTION = "Mình cần nói rõ điều gì trước khi nhận thêm việc?"


def _framed(
    spread_map: TarotSpreadMap,
    *,
    context: TarotContext = TarotContext.WORK,
    voice: TarotVoice = TarotVoice.STRAIGHT_WARM,
    offset: int = 0,
    question: str = QUESTION,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    count = len(_POSITIONS[spread_map])
    return ENGINE.render(
        card_ids=tuple(CARDS[(offset + 7 * i) % 78] for i in range(count)),
        spread=SPREAD[count],
        spread_map=spread_map,
        context=context,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )


# ---------------------------------------------------------------- AC07 roles


def test_ac07_three_cards_read_core_then_pitfall_then_a_step() -> None:
    reading = _framed(TarotSpreadMap.THREE_UNBLOCK)
    clear, missed, step = reading.positions
    fields = [_CardMeaning.for_context(p.card, reading.context) for p in reading.positions]

    assert fields[0].core in clear.meaning_here
    assert fields[1].tension.partition("; đồng thời dễ ")[0] in missed.meaning_here
    assert step.small_action and clear.small_action is None and missed.small_action is None


@pytest.mark.parametrize("spread_map", list(TarotSpreadMap))
@pytest.mark.parametrize("voice", list(TarotVoice))
def test_ac07_every_map_has_one_step_role_and_role_fields(
    spread_map: TarotSpreadMap, voice: TarotVoice
) -> None:
    for offset in range(0, 78, 13):
        reading = _framed(spread_map, voice=voice, offset=offset)
        steps = [p for p in reading.positions if p.small_action]
        assert [p.key for p in steps] == [
            p.key for p in reading.positions if p.key in roles.STEP_ROLES
        ]
        assert len(steps) == 1
        prose = " ".join(p.meaning_here for p in reading.positions).casefold()
        assert "ý chính của lá" not in prose and "ý chính:" not in prose  # no generic branch


# ---------------------------------------------------------------- AC12 cleanup


@pytest.mark.parametrize("context", list(TarotContext))
def test_ac12_role_readings_drop_retired_prefixes(context: TarotContext) -> None:
    for spread_map in TarotSpreadMap:
        for voice in TarotVoice:
            reading = _framed(spread_map, context=context, voice=voice, offset=5)
            for position in reading.positions:
                prose = " ".join(
                    (position.meaning_here, position.everyday_scene, position.small_action or "")
                ).casefold()
                assert not any(prefix in prose for prefix in roles.RETIRED_PREFIXES)
                assert not position.everyday_scene.casefold().startswith("ví dụ")


def test_ac12_scene_label_removal_keeps_the_sentence() -> None:
    assert roles.scene_without_label("Ví dụ: Có lần bạn chờ.") == "Có lần bạn chờ."
    assert roles.scene_without_label("Khi gần hạn, bạn chờ.") == "Khi gần hạn, bạn chờ."


# ---------------------------------------------------------------- AC13 gates


def _sample(surface: Literal["daily", "tarot"], scene: str, action: str) -> ReviewSample:
    return ReviewSample(
        persona_id="t",
        surface=surface,
        sections=(("headline", "Một điều rõ."), ("scene_0", scene), ("action_0", action)),
        disclaimer="Một góc tự soi.",
        provenance_ids=("pollack-78-degrees",),
        evidence_validated=True,
    )


def test_ac13_tarot_has_no_minimum_length_but_keeps_markers() -> None:
    agent = ContentReviewAgent()
    short = agent.review((_sample("tarot", "Khi gần hạn, bạn chờ.", "Viết điều đã được nói."),))
    assert not [
        f for f in short.findings if f.rule_id in {"scene-not-observable", "action-not-testable"}
    ]
    unmarked = agent.review((_sample("tarot", "Một chuyện mơ hồ.", "Thở đều."),))
    assert {f.rule_id for f in unmarked.findings} >= {"scene-not-observable", "action-not-testable"}
    daily = agent.review((_sample("daily", "Khi gần hạn, bạn chờ.", "Viết điều đã được nói."),))
    assert {f.rule_id for f in daily.findings} >= {"scene-not-observable", "action-not-testable"}


def _tampered(reading: TarotReading, index: int, **changes: Any) -> TarotReading:
    positions = list(reading.positions)
    positions[index] = positions[index].model_copy(update=changes)
    return reading.model_copy(update={"positions": tuple(positions)})


def test_ac13_role_fit_rejects_actions_and_fields_outside_their_role() -> None:
    reading = _framed(TarotSpreadMap.THREE_UNBLOCK)
    ENGINE.validate(reading)
    with pytest.raises(TarotContentRejected, match="small action"):
        ENGINE.validate(_tampered(reading, 0, small_action="Viết điều đã được nói."))
    with pytest.raises(TarotContentRejected, match="small action"):
        ENGINE.validate(_tampered(reading, 2, small_action=None))
    with pytest.raises(TarotContentRejected, match="role's field"):
        ENGINE.validate(_tampered(reading, 1, meaning_here="Một ý chung chung về công việc."))
    with pytest.raises(TarotContentRejected, match="retired filler"):
        ENGINE.validate(
            _tampered(reading, 0, everyday_scene=f"Ví dụ: {reading.positions[0].everyday_scene}")
        )


def test_ac13_no_decision_or_prediction() -> None:
    reading = _framed(TarotSpreadMap.FIVE_CHOICE)
    ENGINE.validate(reading)
    for headline in ("Bạn nên chọn hướng A.", "Chuyện này rồi sẽ thành công."):
        with pytest.raises(TarotContentRejected, match="decides or predicts"):
            ENGINE.validate(reading.model_copy(update={"headline": headline}))
    # A card's pitfall may name a feared prediction without the reading making one.
    quoting = _framed(TarotSpreadMap.THREE_UNBLOCK, context=TarotContext.GENERAL)
    ENGINE.validate(quoting)


# ---------------------------------------------------------------- compatibility (AC17)

# 36 legacy readings (3 questions x 4 voices x 1/3/5 cards), canonical JSON, computed on the
# approved B2-1 head 9c28725 and unchanged by B2-2.
LEGACY_GOLDEN = "412f37f9fad21b9d785d2dff45aeda3a016bc89598b9901d6c9e11261a4b8d13"


def test_sessions_without_a_frame_render_byte_identically() -> None:
    questions = (
        ("Mình nên nhìn rõ điều gì trước khi nhắn lại?", TarotContext.RELATIONSHIPS),
        ("Lúc nào mình có người yêu?", TarotContext.GENERAL),
        (QUESTION, TarotContext.WORK),
    )
    out = []
    for question, context in questions:
        for voice in TarotVoice:
            for spread, count in (
                (TarotSpread.ONE_CARD, 1),
                (TarotSpread.THREE_CARD, 3),
                (TarotSpread.FIVE_CARD, 5),
            ):
                reading = ENGINE.render(
                    card_ids=tuple(CARDS[5 : 5 + count]),
                    spread=spread,
                    context=context,
                    question=question,
                    voice=voice,
                )
                out.append(
                    json.dumps(reading.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
                )
    assert hashlib.sha256("\n".join(out).encode()).hexdigest() == LEGACY_GOLDEN


def test_a_stored_v6_reading_still_validates() -> None:
    legacy = ENGINE.render(
        card_ids=tuple(CARDS[:3]),
        spread=TarotSpread.THREE_CARD,
        context=TarotContext.WORK,
        question=QUESTION,
        voice=TarotVoice.PLAYFUL_GROUNDED,
    )
    stored = json.loads(json.dumps(legacy.model_dump(mode="json")))
    restored = TarotReading.model_validate(stored)
    assert all(position.small_action for position in restored.positions)
    assert restored.provenance.gate_version == "tarot-gates-v4"


# ---------------------------------------------------------------- service and provider payload


def test_service_three_card_session_reads_by_role_and_payload_stays_closed() -> None:
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.domains.tarot.models import TarotSessionView
    from app.domains.tarot.rewrite import compile_tarot_rewrite_request
    from app.main import create_app
    from tests.tarot.test_question_frame import _payload

    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as test_client:
        guest = test_client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "tarot-reflection-v1",
                "purpose": "tarot_reflection",
                "idempotency_key": "tarot-roles-guest-1234567890",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        started = test_client.post(
            "/v1/tarot/sessions",
            headers=headers,
            json={
                "context": "work",
                "question": f"{QUESTION} zqcanary7tim",
                "spread": "three_card",
                "origin": "direct",
                "idempotency_key": "tarot-roles-start-1234567890",
            },
        ).json()
        view = None
        for index, fan in enumerate((3, 30, 60)):
            response = test_client.put(
                f"/v1/tarot/sessions/{started['id']}/selections",
                headers=headers,
                json={"fan_index": fan, "expected_version": started["version"] + index},
            )
            assert response.status_code == 200, response.text
            view = TarotSessionView.model_validate(response.json())
        assert view is not None and view.reading is not None
        actions = [position.small_action for position in view.reading.positions]
        assert actions[0] is None and actions[1] is None and actions[2]
        assert view.reading.provenance.gate_version == "tarot-gates-v5"

        guest_id, _ = _payload(test_client)
        request = compile_tarot_rewrite_request(
            guest_id, view, model_version="gpt-6-luna", prompt_version="surface-rewrite-v1"
        )
        assert request is not None
        positions = cast(list[dict[str, Any]], request.safe_payload["positions"])
        assert [p["small_action"] for p in positions][:2] == [None, None]
        outbound = json.dumps(request.model_dump(mode="json"), ensure_ascii=False)
        assert "zqcanary7tim" not in outbound
