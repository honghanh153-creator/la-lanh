"""B2-4b: machine items of the psychology checklist for framed Tarot readings (US-20 AC14).

The owner reads the samples in docs/reviews/2026-10-18-b2-tarot-copy-review.xlsx for the rest.
"""

from __future__ import annotations

import pytest

from app.domains.tarot import checklist, stance
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.models import TarotContext, TarotSpreadMap, TarotVoice
from tests.tarot.test_provenance import _reading


@pytest.mark.parametrize("table", [stance.HEADLINES, stance.ROAST_HEADLINES])
def test_ac14_no_headline_frame_gives_advice(table: dict[str, tuple[str, str, str]]) -> None:
    for key, frames in table.items():
        for template in frames:
            # The frame's own words (slots blanked) must not advise ...
            assert not checklist.template_gives_advice(template), (key, template)
            # ... and every filled frame is recognised as that approved frame.
            for action in (*stance.ACTION_PHRASES.values(), stance.GENERIC_ACTION):
                text = template.format(
                    action=action,
                    topic="công việc",
                    target=action,
                )
                assert not checklist.headline_gives_advice(text), (key, template, action)


@pytest.mark.parametrize(
    ("text", "advice"),
    [
        ("Mặt Trời: hãy nhắn ngay.", True),
        ("Với Mặt Trời, nên cân nhắc thêm trước khi gửi đi.", True),
        ("Mặt Trời: cân nhắc thêm trước khi gửi đi, đừng vội.", True),
        ("Điều cần sẵn sàng trước khi thử lại.", False),  # an approved frame and action phrase
        ("Mặt Trời: các lá nghiêng về thử nhắn lại.", False),  # the stance marker
        ("Mặt Trời: thử lại đi.", True),  # a bare action phrase is advice (Codex #27)
        ("Mặt Trời: chuyện thử lại đi.", True),
        ("Hãy nhắn: các lá nghiêng về thử nhắn lại.", True),  # not a card title
    ],
)
def test_ac14_headline_advice_detector(text: str, advice: bool) -> None:
    assert checklist.headline_gives_advice(text) is advice


@pytest.mark.parametrize(
    ("text", "coercive"),
    [
        ("Bạn phải nói ngay hôm nay.", True),
        ("Chuyện này nhất định sẽ ổn.", True),
        ("Nói đi, nếu không thì mất cơ hội.", True),
        ("Tóm gọn nhẹ nhàng, không ai bắt bạn phải gồng đâu.", False),
        ("Không ai bắt bạn phải gồng đâu.", False),
        ("Lá bắt bạn phải nói ngay.", True),  # positive force (Codex #27)
        ("Tôi bắt bạn phải nhận thêm việc.", True),
        ("Việc này không bắt buộc.", False),
    ],
)
def test_ac14_coercion_detector(text: str, coercive: bool) -> None:
    assert bool(checklist.COERCION.search(text.lower())) is coercive


@pytest.mark.parametrize("voice", list(TarotVoice))
@pytest.mark.parametrize("context", [TarotContext.WORK, TarotContext.SELF_CARE])
def test_ac14_readings_pass_the_gated_items_and_end_on_the_step(
    voice: TarotVoice, context: TarotContext
) -> None:
    for seed in range(4):
        for spread_map in TarotSpreadMap:
            reading = _reading(
                "Mình có nên nghỉ ngơi sớm hơn tối nay không?",
                spread_map,
                context=context,
                voice=voice,
                seed=seed,
            )
            result = checklist.check(reading)
            assert result.gated_ok, (spread_map, voice, result)


# ---------------------------------------------------------------- Codex P2 regressions (#27)

HOW = "Làm thế nào để mình chia việc rõ hơn với nhóm?"


@pytest.mark.parametrize(
    "closing", ["Lá bắt bạn phải nói ngay.", "Tôi bắt bạn phải nhận thêm việc."]
)
def test_ac14_positive_force_fails_the_checklist(closing: str) -> None:
    reading = _reading(HOW, TarotSpreadMap.THREE_UNBLOCK).model_copy(
        update={"closing_prompt": closing}
    )
    TarotReadingEngine.validate(reading)  # the engine's own gates let it through
    assert not checklist.check(reading).gated_ok


def test_ac14_bare_action_headline_fails_the_checklist() -> None:
    reading = _reading(HOW, TarotSpreadMap.THREE_UNBLOCK)
    reading = reading.model_copy(
        update={"headline": f"{reading.positions[-1].card.title_vi}: thử lại đi."}
    )
    TarotReadingEngine.validate(reading)
    assert not checklist.check(reading).gated_ok


def test_ac14_negated_force_is_still_allowed() -> None:
    reading = _reading(HOW, TarotSpreadMap.THREE_UNBLOCK).model_copy(
        update={"closing_prompt": "Không ai bắt bạn phải gồng đâu."}
    )
    TarotReadingEngine.validate(reading)
    assert checklist.check(reading).gated_ok


# ------------------------------------------------------------- Codex P2 regression (#27 @ f7b0798)

RETRY = "Làm thế nào để mình thử lại việc này?"  # HOW + thu_lai


@pytest.mark.parametrize("voice", list(TarotVoice))
@pytest.mark.parametrize("seed", range(3))
def test_ac14_one_card_how_headline_with_an_action_is_an_approved_frame(
    voice: TarotVoice, seed: int
) -> None:
    reading = _reading(RETRY, TarotSpreadMap.ONE_FOCUS, voice=voice, seed=seed)
    TarotReadingEngine.validate(reading)
    # Renderer v9 (owner, 29/10/2026): headlines name no card.
    assert reading.positions[0].card.title_vi not in reading.headline
    assert "thử lại" in reading.headline
    result = checklist.check(reading)
    assert not result.headline_advice and result.gated_ok, reading.headline


@pytest.mark.parametrize("voice", list(TarotVoice))
def test_ac14_multi_card_how_headline_still_matches_and_bare_imperative_fails(
    voice: TarotVoice,
) -> None:
    reading = _reading(RETRY, TarotSpreadMap.THREE_UNBLOCK, voice=voice)
    assert not any(p.card.title_vi in reading.headline for p in reading.positions)
    assert checklist.check(reading).gated_ok, reading.headline
    title = reading.positions[0].card.title_vi
    for bare in ("Thử lại đi.", f"{title}: thử lại đi.", f"{title} và {title}: thử lại đi."):
        assert checklist.headline_gives_advice(bare), bare
