"""A typed question becomes closed labels; outcome questions never get a yes or no."""

from __future__ import annotations

import pytest

from app.domains.month_answer.facts import Topic
from app.domains.month_answer.question import QuestionKind, read_question

# Synthetic questions in the style the 100-persona panel asked for (20.11.2026).
CASES: tuple[tuple[str, Topic | None, QuestionKind], ...] = (
    ("Làm sao nói với sếp là mình đang quá tải?", Topic.WORK, QuestionKind.HOW),
    ("Buổi phỏng vấn sắp tới mình nên chuẩn bị gì?", Topic.WORK, QuestionKind.HOW),
    ("Buổi phỏng vấn tới mình có đậu không?", Topic.WORK, QuestionKind.OUTCOME),
    ("Hết thử việc tháng này mình có được ký hợp đồng không?", Topic.WORK, QuestionKind.OUTCOME),
    ("Cuối tháng này mình có đủ tiền ăn không?", Topic.MONEY, QuestionKind.OUTCOME),
    ("Tuần nào tháng này nên nhập hàng nhiều?", Topic.MONEY, QuestionKind.TIMING),
    ("Hàng tồn tháng này nên xả thế nào?", Topic.MONEY, QuestionKind.HOW),
    ("Làm sao nói chuyện lại với bố mẹ cho bớt căng?", Topic.FAMILY, QuestionKind.HOW),
    ("Ba mẹ có thật sự buồn vì mình không?", Topic.FAMILY, QuestionKind.OTHER_MIND),
    ("Mình có nên nhắn lại người cũ không?", Topic.LOVE, QuestionKind.SHOULD),
    ("Bao giờ mình mới gặp được người hợp?", Topic.LOVE, QuestionKind.TIMING),
    ("Học kỳ này mình có giữ được học bổng không?", Topic.STUDY, QuestionKind.OUTCOME),
    ("Ba môn thi trong hai tuần thì chia ôn thế nào?", Topic.STUDY, QuestionKind.HOW),
    ("Cuối tuần nhớ nhà quá thì làm gì?", Topic.MIND, QuestionKind.HOW),
    ("Hôm nay bực sếp quá, làm gì cho nguôi?", Topic.MIND, QuestionKind.HOW),
    ("lam sao noi voi sep la minh dang qua tai", Topic.WORK, QuestionKind.HOW),
    ("Có phải mình chưa đủ tốt không?", Topic.MIND, QuestionKind.OUTCOME),
    ("Tháng này thế nào nhỉ?", None, QuestionKind.HOW),
)


@pytest.mark.parametrize(("text", "topic", "kind"), CASES)
def test_labels(text: str, topic: Topic | None, kind: QuestionKind) -> None:
    labels = read_question(text)
    assert labels.topic is topic
    assert labels.kind is kind


def test_same_text_same_labels() -> None:
    for text, _topic, _kind in CASES:
        assert read_question(text) == read_question(text)


def test_labels_hold_no_text() -> None:
    labels = read_question("Làm sao nói với sếp zqcanary7month là mình đang quá tải?")
    assert "zqcanary7month" not in repr(labels)
