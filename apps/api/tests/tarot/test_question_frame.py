"""B2-1: understanding a Tarot question (US-20 AC01-AC06).

Task: docs/plans/2026-10-17-b2-1-tarot-question-frame-task.md.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.domains.tarot import question_frame as qf
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import (
    QuestionFrame,
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotSessionView,
    TarotSpread,
    TarotVoice,
)
from app.domains.tarot.rewrite import compile_tarot_rewrite_request
from app.domains.tarot.tables import TarotSessionRow
from app.main import create_app

BANK = Path(__file__).resolve().parents[4] / "docs" / "fixtures" / "tarot-question-bank-v1.json"
ITEMS: list[dict[str, Any]] = json.loads(BANK.read_text())["items"]
ENGINE = TarotReadingEngine()
CLARIFY = "Câu hỏi cần thêm một tình huống cụ thể"
OUTCOME_EXPLANATION = {
    "clarify": CLARIFY,
    "reject_high_stakes": "Tarot không thay thế dữ kiện hay chuyên gia",
    "reject_third_party_mind": "Lá Hỏi không đoán đầu người khác",
    "reject_certainty": "Câu hỏi đang tìm một kết luận chắc chắn",
}


def _assess(question: str, context: TarotContext = TarotContext.GENERAL) -> Any:
    return ENGINE.assess_question(question, context)


# ---------------------------------------------------------------- AC01 form


def test_ac01_every_labelled_bank_question_gets_its_form() -> None:
    labelled = [item for item in ITEMS if item.get("form")]
    correct = sum(qf.classify_form(item["question"]).value == item["form"] for item in labelled)
    assert len(labelled) == 289
    assert correct / len(labelled) >= 0.95


@pytest.mark.parametrize(
    ("question", "form"),
    [
        # Held out from the bank: the rules must not be tuned to its wording only.
        ("Mình có nên đổi chỗ ngồi trong lớp không?", TarotQuestionForm.YES_NO),
        ("Có nên rủ em gái đi xem phim hay để dịp khác không?", TarotQuestionForm.YES_NO),
        ("Đi bộ hay đạp xe tới trường thì hợp với mình hơn?", TarotQuestionForm.CHOICE),
        ("Giữa học nhóm và tự học, cách nào giúp mình nhớ lâu?", TarotQuestionForm.CHOICE),
        ("Làm sao để mình bớt ngại khi thuyết trình?", TarotQuestionForm.HOW),
        ("Tại sao mình hay hoãn việc dọn tủ quần áo?", TarotQuestionForm.WHY),
        ("Lúc nào mình nên nói với nhóm về kế hoạch mới?", TarotQuestionForm.TIMING),
        ("Mình cần để ý gì trong buổi gặp mặt sắp tới?", TarotQuestionForm.OPEN),
    ],
)
def test_ac01_held_out_questions(question: str, form: TarotQuestionForm) -> None:
    assert qf.classify_form(question) is form


# ---------------------------------------------------------------- AC02 topic


def test_ac02_edge_topics_are_scored_from_several_signals() -> None:
    edges = [item for item in ITEMS if item["id"].startswith("edge.")]
    assert len(edges) == 8
    for item in edges:
        topic = qf.score_topic(item["question"], TarotContext(item["context"]))
        assert topic.value == item["expected"]["topic"], item["id"]


def test_ac02_asking_is_not_automatically_communication() -> None:
    question = "Mình có nên hỏi sếp về lịch nghỉ phép trước hạn chót không?"
    assert qf.score_topic(question, TarotContext.GENERAL) is TarotContext.WORK
    # A tie keeps the topic the reader chose.
    assert qf.score_topic("Mình có nên thử một việc mới không?", TarotContext.ENERGY) is (
        TarotContext.ENERGY
    )
    # Strong evidence for another topic outweighs the chosen one.
    assert (
        qf.score_topic(
            "Có nên nói thẳng trong tin nhắn hay gọi điện để trò chuyện?", TarotContext.WORK
        )
        is TarotContext.COMMUNICATION
    )


# ---------------------------------------------------------------- AC03 / AC04 boundaries


def test_ac03_ac04_every_bank_rejection_is_refused_with_a_reframe_in_filter_order() -> None:
    """Every rejection is refused with a reframe. Its category is the expected one or an
    earlier filter in the mandated order (e.g. "Họ có quay lại ...?" also asks another
    person's mind, which is checked before certainty, as before B2-1)."""

    order = list(OUTCOME_EXPLANATION)
    rejected = [item for item in ITEMS if not item["expected"]["accepted"]]
    assert len(rejected) == 32
    for item in rejected:
        assessment = _assess(item["question"])
        assert assessment.accepted is False, item["id"]
        assert assessment.suggested_reframe, item["id"]
        actual = next(
            outcome
            for outcome, prefix in OUTCOME_EXPLANATION.items()
            if assessment.explanation.startswith(prefix)
        )
        assert order.index(actual) <= order.index(item["expected"]["outcome"]), item["id"]
    vague = [item for item in rejected if item["expected"]["outcome"] == "clarify"]
    assert all(_assess(item["question"]).explanation.startswith(CLARIFY) for item in vague)


def test_ac03_filter_order_is_short_then_high_stakes_then_mind_then_certainty() -> None:
    assert _assess("Bệnh à?").explanation.startswith(CLARIFY)
    assert _assess("Anh ấy có bệnh gì không?").explanation.startswith(
        OUTCOME_EXPLANATION["reject_high_stakes"]
    )
    assert _assess("Anh ấy có chắc chắn thích mình không?").explanation.startswith(
        OUTCOME_EXPLANATION["reject_third_party_mind"]
    )


def test_ac04_vague_questions_ask_for_a_situation_and_real_ones_pass() -> None:
    for question in ("Tình yêu và công việc", "Chuyện tình cảm của mình", "Ổn không?"):
        assert _assess(question).explanation.startswith(CLARIFY), question
    accepted = [item for item in ITEMS if item["expected"]["accepted"]]
    assert all(_assess(i["question"], TarotContext(i["context"])).accepted for i in accepted)
    assert _assess("Mình có nên nhắn cho họ trước không?", TarotContext.RELATIONSHIPS).accepted


# ---------------------------------------------------------------- AC05 timing -> readiness


def test_ac05_own_timing_is_answered_as_readiness_in_every_voice() -> None:
    timing = [item for item in ITEMS if item.get("form") == "timing"]
    assert len(timing) == 49
    assert all(_assess(i["question"], TarotContext(i["context"])).accepted for i in timing)

    cards = tuple(card.id for card in all_cards())
    question = "Khi nào mình nên nghỉ việc?"
    assessment = _assess(question, TarotContext.WORK)
    assert assessment.frame.form is TarotQuestionForm.TIMING
    for voice in TarotVoice:
        for spread, count in ((TarotSpread.ONE_CARD, 1), (TarotSpread.FIVE_CARD, 5)):
            reading = ENGINE.render(
                card_ids=cards[10 : 10 + count],
                spread=spread,
                context=TarotContext.WORK,
                question=question,
                voice=voice,
                question_intent=assessment.intent,
                frame=assessment.frame,
            )
            assert reading.headline == qf.readiness_headline(voice)
            assert reading.summary.startswith(qf.READINESS_NOTE)
            assert reading.provenance.question_rules_version == qf.QUESTION_RULES_VERSION


@pytest.mark.parametrize(
    "question",
    [
        "Khi nào mình có người yêu?",  # an event, not one's own action
        "Khi nào là lúc người ấy nhắn lại?",
        "Bao giờ người ấy nhắn lại?",  # another person
        "Bao giờ dự án này xong?",
        "Chuyện này chắc chắn sẽ thành công chứ?",
        "Người yêu cũ có quay lại không?",
        "Mọi chuyện sẽ xảy ra theo ý mình không?",
    ],
)
def test_ac05_predictions_stay_rejected(question: str) -> None:
    assert _assess(question).explanation.startswith(OUTCOME_EXPLANATION["reject_certainty"])


# ---------------------------------------------------------------- frame labels


def test_frame_holds_closed_labels_only() -> None:
    assert len(TarotAction) == 30
    frame = _assess("Mình có nên xin lỗi bạn thân trước không?", TarotContext.RELATIONSHIPS).frame
    assert frame == QuestionFrame(
        form=TarotQuestionForm.YES_NO, topic=TarotContext.RELATIONSHIPS, action=TarotAction.XIN_LOI
    )
    with pytest.raises(ValueError):
        QuestionFrame.model_validate({**frame.model_dump(), "question": "x"})
    assert qf.match_action("Mình không muốn xin lỗi, có nên nói rõ lý do không?") is (
        TarotAction.NOI_RA
    )
    assert qf.match_action("Mình có nên hỏi lại sếp về hạn chót không?") is TarotAction.HOI_LAI
    assert qf.match_action("Điều gì đang làm mình thấy xa cách?") is None


# ---------------------------------------------------------------- AC06 + replay (service)


@pytest.fixture
def client() -> Iterator[TestClient]:
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
        yield test_client


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "tarot-reflection-v1",
            "purpose": "tarot_reflection",
            "idempotency_key": "tarot-frame-guest-1234567890",
        },
    )
    return {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": response.json()["csrf_token"]}


def _start(client: TestClient, headers: dict[str, str], question: str, context: str) -> Any:
    response = client.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": context,
            "question": question,
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": "tarot-frame-start-1234567890",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _select(client: TestClient, headers: dict[str, str], started: Any) -> TarotSessionView:
    response = client.put(
        f"/v1/tarot/sessions/{started['id']}/selections",
        headers=headers,
        json={"fan_index": 11, "expected_version": started["version"]},
    )
    assert response.status_code == 200, response.text
    return TarotSessionView.model_validate(response.json())


def _payload(client: TestClient) -> tuple[Any, dict[str, Any]]:
    app = cast(Any, client.app)
    service = app.state.tarot_session_service

    async def load() -> tuple[Any, dict[str, Any]]:
        async with app.state.database.sessions() as database:
            row = (await database.scalars(select(TarotSessionRow))).one()
            return row.guest_id, service._decrypt(row)

    assert client.portal is not None
    return cast(tuple[Any, dict[str, Any]], client.portal.call(load))


def _rewrite_payload(client: TestClient, payload: dict[str, Any]) -> None:
    app = cast(Any, client.app)
    service = app.state.tarot_session_service

    async def store() -> None:
        async with app.state.database.sessions() as database, database.begin():
            row = (await database.scalars(select(TarotSessionRow))).one()
            row.payload_ciphertext = service._encrypt(row.id, payload)

    assert client.portal is not None
    client.portal.call(store)


def test_ac06_frame_lives_only_in_the_encrypted_payload(client: TestClient) -> None:
    headers = _headers(client)
    started = _start(client, headers, "Bao giờ mình nên mở lời xin lỗi?", "relationships")
    _, payload = _payload(client)

    assert payload["question_frame"] == {
        "version": qf.QUESTION_FRAME_VERSION,
        "form": "timing",
        "topic": "relationships",
        "action": "xin_loi",
    }
    assert payload["question_rules_version"] == qf.QUESTION_RULES_VERSION
    view = _select(client, headers, started)
    body = json.dumps(view.model_dump(mode="json"), ensure_ascii=False)
    assert "question_frame" not in body and "xin_loi" not in body
    assert view.reading is not None and view.reading.headline == qf.readiness_headline(view.voice)


def test_frame_is_replayed_not_recomputed_when_rendering(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _headers(client)
    started = _start(client, headers, "Khi nào mình nên nghỉ việc?", "work")

    def fail(*_: object, **__: object) -> QuestionFrame:
        raise AssertionError("the stored frame must be replayed")

    monkeypatch.setattr(qf, "frame_question", fail)
    view = _select(client, headers, started)
    assert view.reading is not None
    assert view.reading.summary.startswith(qf.READINESS_NOTE)


def test_sessions_started_before_b2_1_render_as_before(client: TestClient) -> None:
    headers = _headers(client)
    question = "Mình nên nhìn rõ điều gì trước khi nhắn lại?"
    started = _start(client, headers, question, "relationships")
    _, payload = _payload(client)
    legacy = {k: v for k, v in payload.items() if k != "question_frame"}
    legacy["question_rules_version"] = "tarot-question-rules-v1"
    _rewrite_payload(client, legacy)

    view = _select(client, headers, started)
    assert view.reading is not None
    expected = ENGINE.render(
        card_ids=tuple(position.card.id for position in view.reading.positions),
        spread=view.spread,
        spread_map=view.spread_map,
        context=view.context,
        question=question,
        voice=view.voice,
        question_intent=view.reading.question_intent,
    )
    assert view.reading == expected
    assert view.reading.provenance.question_rules_version == "tarot-question-rules-v1"


def test_ac06_canary_never_reaches_brief_payload_or_logs(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    private = "chị Lan ở phòng 302"
    question = f"Mình có nên kể với {private} về zqcanary7tim trước buổi họp không?"
    caplog.set_level(logging.DEBUG)
    headers = _headers(client)
    started = _start(client, headers, question, "work")
    view = _select(client, headers, started)
    guest_id, payload = _payload(client)

    request = compile_tarot_rewrite_request(
        guest_id, view, model_version="gpt-6-luna", prompt_version="surface-rewrite-v1"
    )
    assert request is not None
    outbound = json.dumps(request.model_dump(mode="json"), ensure_ascii=False).casefold()
    frame = json.dumps(payload["question_frame"], ensure_ascii=False).casefold()
    words = private.casefold().split()
    fragments = [" ".join(words[i : i + 2]) for i in range(len(words) - 1)]
    for text in (outbound, frame, caplog.text.casefold()):
        assert "zqcanary7tim" not in text
        assert not any(fragment in text for fragment in fragments)
