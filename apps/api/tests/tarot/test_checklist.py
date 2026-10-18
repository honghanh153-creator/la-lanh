"""B2-4b: machine items of the psychology checklist for framed Tarot readings (US-20 AC14).

The owner reads the samples in docs/reviews/2026-10-18-b2-tarot-copy-review.xlsx for the rest.
"""

from __future__ import annotations

import pytest

from app.domains.tarot import checklist, stance
from app.domains.tarot.models import TarotContext, TarotSpreadMap, TarotVoice
from tests.tarot.test_provenance import _reading


@pytest.mark.parametrize("table", [stance.HEADLINES, stance.ROAST_HEADLINES])
def test_ac14_no_headline_frame_gives_advice(table: dict[str, tuple[str, str, str]]) -> None:
    for key, frames in table.items():
        for template in frames:
            for action in (*stance.ACTION_PHRASES.values(), stance.GENERIC_ACTION):
                text = template.format(
                    focal="Mặt Trời",
                    pair="Mặt Trời và Hai Gậy",
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
        ("Mặt Trời: điều cần sẵn sàng trước khi thử lại.", False),  # an approved action phrase
        ("Mặt Trời: các lá nghiêng về thử nhắn lại.", False),  # the stance marker
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
