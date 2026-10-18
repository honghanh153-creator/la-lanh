"""B2-3: lean, linked summary and dynamic headline (US-20 AC08-AC11).

Task: docs/plans/2026-10-18-b2-3-tarot-stance-task.md.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import pytest

from app.domains.tarot import stance
from app.domains.tarot.engine import _POSITIONS, TarotContentRejected, TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import (
    TarotAction,
    TarotContext,
    TarotReading,
    TarotSpread,
    TarotSpreadMap,
    TarotStanceKind,
    TarotStanceLevel,
    TarotVoice,
)

ENGINE = TarotReadingEngine()
SPREAD = {1: TarotSpread.ONE_CARD, 3: TarotSpread.THREE_CARD, 5: TarotSpread.FIVE_CARD}
YES_NO = "Mình có nên xin lỗi bạn thân trước không?"
CHOICE = "Nên ở nhà nghỉ hay ra ngoài đi dạo cho đổi gió?"
OPEN = ("major-sun", "major-star", "cups-ace", "pentacles-ace", "wands-ace")
HOLD = ("major-tower", "swords-9", "swords-10", "swords-8", "cups-5")
TWO = ("major-justice", "major-temperance", "major-wheel-of-fortune")


def _render(
    question: str,
    cards: tuple[str, ...],
    spread_map: TarotSpreadMap,
    *,
    context: TarotContext = TarotContext.RELATIONSHIPS,
    voice: TarotVoice = TarotVoice.STRAIGHT_WARM,
) -> TarotReading:
    assessment = ENGINE.assess_question(question, context)
    assert assessment.accepted, question
    return ENGINE.render(
        card_ids=cards,
        spread=SPREAD[len(cards)],
        spread_map=spread_map,
        context=context,
        question=question,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )


# ---------------------------------------------------------------- AC09 labels and weights


def test_ac09_every_card_has_a_lean_within_the_label_budget() -> None:
    ids = {card.id for card in all_cards()}
    assert set(stance.LEAN_DEFAULTS) == ids
    assert {card for card, _ in stance.LEAN_OVERRIDES} <= ids
    assert len(stance.LEAN_DEFAULTS) + len(stance.LEAN_OVERRIDES) <= 468
    assert stance.lean_of("major-lovers", TarotContext.RELATIONSHIPS) is stance.Lean.OPEN
    assert stance.lean_of("major-lovers", TarotContext.WORK) is stance.Lean.TWO_SIDED
    assert (stance.role_weight("next"), stance.role_weight("clear")) == (2.0, 1.0)
    assert stance.role_weight("missed") == 0.5


# ---------------------------------------------------------------- AC08 levels


@pytest.mark.parametrize(
    ("cards", "level"),
    [
        (OPEN[:3], TarotStanceLevel.LEAN_TRY),
        (HOLD[:3], TarotStanceLevel.CONSIDER),
        ((OPEN[0], HOLD[0], TWO[0]), TarotStanceLevel.UNCLEAR),  # 1 - 0.5 + 0 = 0.5
    ],
)
def test_ac08_three_levels_with_reasons_from_roles_and_cards(
    cards: tuple[str, ...], level: TarotStanceLevel
) -> None:
    reading = _render(YES_NO, cards, TarotSpreadMap.THREE_UNBLOCK)
    assert reading.stance is not None
    assert reading.stance.kind is TarotStanceKind.YES_NO
    assert reading.stance.level is level
    assert reading.stance.action is TarotAction.XIN_LOI
    assert 1 <= len(reading.stance.reasons) <= 2
    labels = {p.key: p for p in reading.positions}
    for reason in reading.stance.reasons:
        position = labels[reason.position_key]
        assert reason.card_id == position.card.id
        assert reason.text.startswith(f"{position.label}: {position.card.title_vi}")
    assert "chưa nên" not in reading.stance.conclusion
    if level is TarotStanceLevel.LEAN_TRY:
        assert reading.stance.conclusion == "Các lá nghiêng về thử xin lỗi."


def test_ac08_choice_compares_only_with_two_option_roles() -> None:
    assert stance.split_choice(CHOICE) == (TarotAction.O_NHA, TarotAction.RA_NGOAI)
    five = (OPEN[0], HOLD[0], OPEN[1], TWO[0], OPEN[2])  # need, option_a, option_b, ...
    reading = _render(CHOICE, five, TarotSpreadMap.FIVE_CHOICE, context=TarotContext.ENERGY)
    assert reading.stance is not None
    assert reading.stance.level is TarotStanceLevel.LEAN_TRY
    assert reading.stance.action is TarotAction.RA_NGOAI  # option_b is open, option_a holds
    assert [r.position_key for r in reading.stance.reasons] == ["option_a", "option_b"]

    equal = (OPEN[0], OPEN[1], OPEN[2], TWO[0], HOLD[0])
    tie = _render(CHOICE, equal, TarotSpreadMap.FIVE_CHOICE, context=TarotContext.ENERGY)
    assert tie.stance is not None and tie.stance.level is TarotStanceLevel.UNCLEAR

    three = _render(CHOICE, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK, context=TarotContext.ENERGY)
    assert three.stance is not None and three.stance.level is TarotStanceLevel.CLARIFY_CHOICE
    vague = "Mình nên chọn lớp buổi sáng hay lớp buổi tối?"
    assert stance.split_choice(vague) is None
    unsplit = _render(vague, five, TarotSpreadMap.FIVE_CHOICE, context=TarotContext.WORK)
    assert unsplit.stance is not None
    assert unsplit.stance.level is TarotStanceLevel.CLARIFY_CHOICE


@pytest.mark.parametrize(
    "question",
    [
        "Làm thế nào để mình chia việc rõ hơn với nhóm?",
        "Vì sao mình hay ngại mở lời trước?",
        "Điều gì mình cần nhìn rõ trong mối quan hệ này?",
        "Khi nào mình nên nghỉ việc?",
    ],
)
def test_ac08_other_forms_have_no_stance_and_omit_the_key(question: str) -> None:
    reading = _render(question, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)
    assert reading.stance is None
    assert "stance" not in reading.model_dump(mode="json")


# ---------------------------------------------------------------- AC10 linked summary


@pytest.mark.parametrize("spread_map", list(TarotSpreadMap))
def test_ac10_summary_mentions_every_role_with_n_minus_1_links(spread_map: TarotSpreadMap) -> None:
    cards = tuple(c.id for c in all_cards())[3 : 3 + len(_POSITIONS[spread_map])]
    reading = _render(YES_NO, cards, spread_map)
    from app.domains.tarot.engine import _position_views

    views = _position_views(reading.positions, reading.context)
    assert stance.summary_links(reading.summary, views)
    for view in views:
        assert stance.anchor(view) in reading.summary


def test_ac10_gate_rejects_a_summary_that_drops_a_role_or_its_links() -> None:
    from app.domains.tarot.engine import _position_views

    reading = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)
    unlinked = reading.summary
    for conjunction in stance.ALL_CONJUNCTIONS:
        unlinked = unlinked.replace(f"{conjunction} ", "")
    with pytest.raises(TarotContentRejected, match="link every role"):
        ENGINE.validate(reading.model_copy(update={"summary": unlinked}))
    missing = stance.anchor(_position_views(reading.positions, reading.context)[1])
    dropped = reading.summary.replace(missing, "một ý khác")
    with pytest.raises(TarotContentRejected, match="link every role"):
        ENGINE.validate(reading.model_copy(update={"summary": dropped}))


# ---------------------------------------------------------------- AC09 stance_consistent


def _with_stance(reading: TarotReading, **changes: Any) -> TarotReading:
    assert reading.stance is not None
    return reading.model_copy(update={"stance": reading.stance.model_copy(update=changes)})


def test_ac09_stance_consistent_rejects_tampered_lean_or_prose() -> None:
    reading = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)
    ENGINE.validate(reading)
    with pytest.raises(TarotContentRejected, match="does not match the cards"):
        ENGINE.validate(_with_stance(reading, level=TarotStanceLevel.CONSIDER))
    with pytest.raises(TarotContentRejected, match="headline does not state"):
        focal = reading.positions[2].card.title_vi
        ENGINE.validate(reading.model_copy(update={"headline": f"{focal}: một hướng khác."}))
    with pytest.raises(TarotContentRejected, match="different stance"):
        ENGINE.validate(
            reading.model_copy(update={"summary": f"{reading.summary} Chưa rõ: kéo về hai phía."})
        )


# ---------------------------------------------------------------- AC11 headline


def test_ac11_headline_carries_form_lean_and_focal_card() -> None:
    lean = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)
    focal = lean.positions[2].card.title_vi  # the step role
    assert lean.headline == f"{focal}: các lá nghiêng về thử xin lỗi."
    how = _render(
        "Làm thế nào để mình chia việc rõ hơn với nhóm?",
        OPEN[:3],
        TarotSpreadMap.THREE_UNBLOCK,
        context=TarotContext.WORK,
    )
    assert how.headline.startswith(
        f"{how.positions[2].card.title_vi} và {how.positions[1].card.title_vi}"
    )
    assert all(len(r.headline.split()) <= 18 for r in (lean, how))
    # B2-4 (AC19): Roast has its own headline frames, still with the focal card and the marker.
    roast = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK, voice=TarotVoice.ROAST)
    assert roast.headline == f"{focal} bật đèn xanh nhẹ: nghiêng về thử xin lỗi."


# ---------------------------------------------------------------- service, API and payload


def test_service_exposes_stance_and_keeps_it_out_of_the_provider_payload() -> None:
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
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "tarot-reflection-v1",
                "purpose": "tarot_reflection",
                "idempotency_key": "tarot-stance-guest-1234567890",
            },
        )
        headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
        started = client.post(
            "/v1/tarot/sessions",
            headers=headers,
            json={
                "context": "relationships",
                "question": YES_NO,
                "spread": "one_card",
                "origin": "direct",
                "idempotency_key": "tarot-stance-start-1234567890",
            },
        ).json()
        response = client.put(
            f"/v1/tarot/sessions/{started['id']}/selections",
            headers=headers,
            json={"fan_index": 9, "expected_version": started["version"]},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["reading"]["stance"]["kind"] == "yes_no"
        view = TarotSessionView.model_validate(body)
        guest_id, _ = _payload(client)
        request = compile_tarot_rewrite_request(
            guest_id, view, model_version="gpt-6-luna", prompt_version="surface-rewrite-v1"
        )
        assert request is not None
        assert "stance" not in json.dumps(request.model_dump(mode="json"))


# ---------------------------------------------------------------- Codex P2 regressions (#25)

LONG_TIMING = "Khi nào mình nên chọn ở lại để nhận thêm việc?"
LONG_CASES = (
    (
        TarotContext.SELF_CARE,
        (
            "pentacles-7",
            "pentacles-king",
            "major-high-priestess",
            "major-hanged-man",
            "major-hierophant",
        ),
    ),
    (
        TarotContext.ENERGY,
        ("swords-page", "cups-2", "major-high-priestess", "wands-king", "major-fool"),
    ),
)


@pytest.mark.parametrize(("context", "cards"), LONG_CASES)
@pytest.mark.parametrize("voice", list(TarotVoice))
def test_p2_1_long_cards_plus_readiness_fit_the_budget(
    context: TarotContext, cards: tuple[str, ...], voice: TarotVoice
) -> None:
    from app.domains.tarot import question_frame
    from app.domains.tarot.engine import _position_views

    assessment = ENGINE.assess_question(LONG_TIMING, context)
    reading = ENGINE.render(
        card_ids=cards,
        spread=TarotSpread.FIVE_CARD,
        context=context,
        question=LONG_TIMING,
        voice=voice,
        question_intent=assessment.intent,
        frame=assessment.frame,
    )
    assert reading.spread_map is TarotSpreadMap.FIVE_CHOICE
    assert reading.summary.startswith(question_frame.READINESS_NOTE)
    assert len(reading.summary.split()) <= 180
    assert stance.summary_links(reading.summary, _position_views(reading.positions, context))


THREE_WAY = (
    "Mình nên chọn ở nhà nghỉ hay ra ngoài đi dạo hay học thêm?",
    "Giữa ở nhà nghỉ và ra ngoài đi dạo và học thêm, mình nên chọn hướng nào?",
    # A comma does not end the list of alternatives (Codex #25 @ ebcb101).
    "Giữa ở nhà nghỉ và ra ngoài đi dạo, và học thêm, mình nên chọn hướng nào?",
    "Nên ở nhà nghỉ hay ra ngoài đi dạo, và học thêm?",
)


@pytest.mark.parametrize("question", THREE_WAY)
def test_p2_2_three_alternatives_never_become_an_a_b_lean(question: str) -> None:
    assert stance.split_choice(question) is None
    cards = ("major-sun", "major-tower", "major-star", "major-justice", "cups-ace")
    reading = _render(question, cards, TarotSpreadMap.FIVE_CHOICE, context=TarotContext.ENERGY)
    assert reading.stance is not None
    assert reading.stance.level is TarotStanceLevel.CLARIFY_CHOICE
    assert stance.split_choice(CHOICE) == (TarotAction.O_NHA, TarotAction.RA_NGOAI)  # control


def test_p2_3_a_conflicting_reason_is_rejected_even_with_its_citation() -> None:
    reading = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)
    assert reading.stance is not None and reading.stance.level is TarotStanceLevel.LEAN_TRY
    first = reading.stance.reasons[0]
    tampered = first.model_copy(
        update={"text": f"{first.text} Các lá gợi ý cân nhắc thêm trước khi xin lỗi."}
    )
    with pytest.raises(TarotContentRejected, match="does not match the cards"):
        ENGINE.validate(_with_stance(reading, reasons=(tampered, *reading.stance.reasons[1:])))
    with pytest.raises(TarotContentRejected, match="different stance"):
        ENGINE.validate(
            reading.model_copy(
                update={"closing_prompt": "Các lá gợi ý cân nhắc thêm trước khi xin lỗi?"}
            )
        )


def test_p2_3_rewrite_with_a_contrary_closing_is_refused() -> None:
    from app.domains.tarot.rewrite import rewrite_tarot_reading

    reading = _render(YES_NO, OPEN[:3], TarotSpreadMap.THREE_UNBLOCK)

    def output(closing: str) -> dict[str, Any]:
        return {
            "headline": reading.headline,
            "synthesis": reading.summary,
            "closing_question": closing,
            "position_readings": [
                {"position_key": p.key, "reading": f"{p.card.title_vi}: {p.meaning_here}"}
                for p in reading.positions
            ],
        }

    assert rewrite_tarot_reading(reading, output("Bạn muốn thử điều nào trước?")) is not None
    refused = rewrite_tarot_reading(
        reading, output("Các lá gợi ý cân nhắc thêm trước khi xin lỗi?")
    )
    assert refused is None


def test_p2_service_long_draw_and_three_way_choice_complete_with_a_reading() -> None:
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.domains.tarot.models import TarotSessionView
    from app.main import create_app
    from tests.tarot.test_question_frame import _payload, _rewrite_payload

    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    cases = (
        (LONG_TIMING, "self_care", LONG_CASES[0][1], None),
        (
            THREE_WAY[0],
            "energy",
            ("major-sun", "major-tower", "major-star", "major-justice", "cups-ace"),
            "clarify_choice",
        ),
        (
            THREE_WAY[2],  # "Giữa A và B, và C, ..."
            "energy",
            ("major-sun", "major-tower", "major-star", "major-justice", "cups-ace"),
            "clarify_choice",
        ),
    )
    for index, (question, context, cards, level) in enumerate(cases):
        with TestClient(app, base_url="http://127.0.0.1:5173") as client:
            guest = client.post(
                "/v1/guest-sessions",
                json={
                    "consent_version": "tarot-reflection-v1",
                    "purpose": "tarot_reflection",
                    "idempotency_key": f"tarot-stance-p2-guest-{index}-1234567890",
                },
            )
            headers = {
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            }
            started = client.post(
                "/v1/tarot/sessions",
                headers=headers,
                json={
                    "context": context,
                    "question": question,
                    "spread": "five_card",
                    "origin": "direct",
                    "idempotency_key": f"tarot-stance-p2-start-{index}-1234567890",
                },
            ).json()
            # Synthetic deck: put the chosen cards first so fan indices 0-4 draw them.
            _, payload = _payload(client)
            deck = list(cards) + [card for card in payload["deck_order"] if card not in cards]
            _rewrite_payload(client, {**payload, "deck_order": deck})
            view = None
            for pick in range(5):
                response = client.put(
                    f"/v1/tarot/sessions/{started['id']}/selections",
                    headers=headers,
                    json={"fan_index": pick, "expected_version": started["version"] + pick},
                )
                assert response.status_code == 200, response.text
                view = TarotSessionView.model_validate(response.json())
            assert view is not None and view.state.value == "complete"
            assert view.reading is not None, question
            assert [p.card.id for p in view.reading.positions] == list(cards)
            if level:
                assert view.reading.stance is not None
                assert view.reading.stance.level.value == level


# Codex parser census (#25 @ ebcb101): 3 closed actions permuted across 4 shapes, 24 cases.
_CENSUS_ACTS = ("ở nhà nghỉ", "ra ngoài đi dạo", "học thêm")
_CENSUS_SHAPES = (
    ("Giữa {a} và {b}, mình nên chọn hướng nào?", True),
    ("Giữa {a} và {b} và {c}, mình nên chọn hướng nào?", False),
    ("Giữa {a} và {b}, và {c}, mình nên chọn hướng nào?", False),
    ("Giữa {a} và {b}, hoặc {c}, mình nên chọn hướng nào?", False),
)


@pytest.mark.parametrize("order", list(itertools.permutations(_CENSUS_ACTS)))
@pytest.mark.parametrize(("shape", "compare"), _CENSUS_SHAPES)
def test_p2_choice_arity_census(order: tuple[str, str, str], shape: str, compare: bool) -> None:
    a, b, c = order
    assert (stance.split_choice(shape.format(a=a, b=b, c=c)) is not None) is compare


def test_p2_bank_choice_coverage_is_unchanged() -> None:
    bank = json.loads(
        (
            Path(__file__).resolve().parents[4] / "docs/fixtures/tarot-question-bank-v1.json"
        ).read_text()
    )
    choices = [i for i in bank["items"] if i.get("form") == "choice"]
    assert sum(1 for i in choices if stance.split_choice(i["question"])) == 11
