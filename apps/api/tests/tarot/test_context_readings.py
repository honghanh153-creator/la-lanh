import re

import pytest

from app.domains.readings.review_agent import (
    ACTION_MARKERS,
    OPAQUE_CORE_FRAGMENTS,
    SCENE_MARKERS,
)
from app.domains.tarot.context_readings import CONTEXT_READINGS, CONTEXT_SCENES
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import TarotContext

CONTEXTS = (
    TarotContext.WORK.value,
    TarotContext.COMMUNICATION.value,
    TarotContext.ENERGY.value,
    TarotContext.SELF_CARE.value,
)
CARD_IDS = tuple(card.id for card in all_cards())


def test_only_requested_contexts_are_authored() -> None:
    assert set(CONTEXT_READINGS) == set(CONTEXTS)
    assert set(CONTEXT_SCENES) == set(CONTEXTS)


@pytest.mark.parametrize("context", CONTEXTS)
def test_every_context_covers_exactly_the_78_card_ids(context: str) -> None:
    assert len(CARD_IDS) == len(set(CARD_IDS)) == 78
    assert set(CONTEXT_READINGS[context]) == set(CARD_IDS)
    assert set(CONTEXT_SCENES[context]) == set(CARD_IDS)


@pytest.mark.parametrize("context", CONTEXTS)
@pytest.mark.parametrize("card_id", CARD_IDS)
def test_entries_have_three_readable_fields_and_a_labelled_example(
    context: str, card_id: str
) -> None:
    reading = CONTEXT_READINGS[context][card_id]
    assert isinstance(reading, tuple)
    assert len(reading) == 3
    assert len(set(reading)) == 3
    for field in reading:
        assert isinstance(field, str)
        assert field == field.strip()
        assert field
    scene = CONTEXT_SCENES[context][card_id]
    assert isinstance(scene, str)
    assert scene == scene.strip()
    assert scene.startswith("Ví dụ: ")
    assert scene.removeprefix("Ví dụ: ").strip()
    assert len(scene.removeprefix("Ví dụ: ").split()) >= 12
    assert any(marker in scene.lower() for marker in SCENE_MARKERS)
    assert any(marker in reading[2].lower() for marker in ACTION_MARKERS)
    for field in (*reading, scene):
        assert not any(fragment in field.lower() for fragment in OPAQUE_CORE_FRAGMENTS)
        assert all(len(sentence.split()) <= 28 for sentence in re.split(r"[.!?]+", field))


@pytest.mark.parametrize("card_id", CARD_IDS)
def test_card_is_reauthored_for_each_context(card_id: str) -> None:
    readings = [CONTEXT_READINGS[context][card_id] for context in CONTEXTS]
    assert len(set(readings)) == 4
    for index in range(3):
        assert len({reading[index] for reading in readings}) == 4
    assert len({CONTEXT_SCENES[context][card_id] for context in CONTEXTS}) == 4


@pytest.mark.parametrize("context", CONTEXTS)
def test_cards_do_not_share_rank_or_suit_copy(context: str) -> None:
    readings = CONTEXT_READINGS[context]
    assert len({reading[0] for reading in readings.values()}) == 78
    assert len(set(CONTEXT_SCENES[context].values())) == 78


@pytest.mark.parametrize(
    ("card_id", "work_terms", "communication_terms"),
    (
        ("cups-king", ("nhóm", "quyết định"), ("cảm xúc", "nói")),
        ("wands-3", ("mở rộng", "đề xuất"), ("phản hồi", "hẹn")),
        ("pentacles-6", ("nguồn lực", "phân bổ"), ("lắng nghe", "hai phía")),
    ),
)
def test_reference_cards_have_concrete_topic_specific_meanings(
    card_id: str, work_terms: tuple[str, ...], communication_terms: tuple[str, ...]
) -> None:
    work = " ".join(CONTEXT_READINGS["work"][card_id]).lower()
    communication = " ".join(CONTEXT_READINGS["communication"][card_id]).lower()
    for term in work_terms:
        assert term in work
    for term in communication_terms:
        assert term in communication
    assert "dự án" in CONTEXT_SCENES["work"]["wands-3"].lower()
    assert "tin nhắn" in CONTEXT_SCENES["communication"]["wands-3"].lower()
    assert "giờ" in CONTEXT_SCENES["work"]["pentacles-6"].lower()
    assert "kể" in CONTEXT_SCENES["communication"]["pentacles-6"].lower()
    assert "chia việc" in CONTEXT_SCENES["work"]["cups-king"].lower()


@pytest.mark.parametrize("context", CONTEXTS)
def test_copy_avoids_known_unsafe_or_obscure_phrasing(context: str) -> None:
    text = " ".join(
        field
        for card_id, reading in CONTEXT_READINGS[context].items()
        for field in (*reading, CONTEXT_SCENES[context][card_id])
    ).lower()
    forbidden = (
        "nhịp",
        "vùng mờ",
        "lớp nhìn",
        "năng lượng vũ trụ",
        "chắc chắn sẽ",
        "số phận",
        "định mệnh",
        "đọc được suy nghĩ",
        "ngừng thuốc",
        "bỏ thuốc",
        "dừng thuốc",
        "chẩn đoán",
        "chữa khỏi",
    )
    assert not any(phrase in text for phrase in forbidden)
    assert not re.search(r"\b(?:trầm cảm|rối loạn|bệnh lý)\b", text)
