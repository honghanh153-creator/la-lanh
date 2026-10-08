from __future__ import annotations

import json

import pytest

from app.domains.content_rewrite.models import RewriteSurface
from app.infrastructure.generation.privacy import (
    PrivacyMinimiser,
    UnsafeRewritePayload,
    reduce_tarot_question,
)


def _daily_payload() -> dict[str, object]:
    return {
        "context": "relationships",
        "scene_key": "psychology:missing-context:relationships",
        "action_key": "psychology:ask-one-clear-question",
        "title_meaning": "Chưa rõ thì chưa cần kết luận.",
        "scene_meaning": "Một tin nhắn ngắn khiến ý của người kia chưa rõ.",
        "action_meaning": "Hỏi lại một câu rõ ràng trước khi kết luận.",
        "requirements": [
            {
                "key": "daily.missing-context",
                "section": "manifestation",
                "markers": ["tin nhắn", "chưa rõ"],
                "min_matches": 1,
            }
        ],
        "evidence": [
            {
                "label": "factor_1",
                "source": "natal",
                "kind": "planet_placement",
                "domain": "communication",
                "role": "primary",
                "confidence": "high",
                "labels": [{"name": "sign", "value": "Song Ngư"}],
            }
        ],
    }


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("birth_date", "1990-03-15"),
        ("birth_time", "07:30"),
        ("birth_place", "Hà Nội"),
        ("email", "an@example.com"),
        ("profile_id", "04727a54-33ab-46ef-9192-3063fecb10f0"),
        ("name", "An"),
    ],
)
def test_minimiser_rejects_raw_identity_and_birth_fields(key: str, value: str) -> None:
    payload = {**_daily_payload(), key: value}

    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(RewriteSurface.DAILY_HOME, payload)


def test_minimiser_emits_only_surface_allowlist() -> None:
    safe = PrivacyMinimiser().minimise(RewriteSurface.DAILY_HOME, _daily_payload())

    assert set(safe) == {
        "context",
        "scene_key",
        "action_key",
        "title_meaning",
        "scene_meaning",
        "action_meaning",
        "requirements",
        "evidence",
    }
    serialized = json.dumps(safe, ensure_ascii=False).lower()
    assert "profile_id" not in serialized
    assert "birth" not in serialized
    assert "longitude" not in serialized


def test_tarot_question_is_locally_classified_without_forwarding_free_text() -> None:
    question = "Người ấy im lặng, mình có nên nhắn lại không?"

    safe = reduce_tarot_question(question, category="relationship")

    assert safe is not None
    assert safe.focus_key == "communication"
    assert question not in safe.model_dump_json()
    assert "người ấy" not in safe.focus_sentence.casefold()


def test_daily_meaning_brief_is_editorial_and_cannot_smuggle_private_context() -> None:
    brief: dict[str, object] = {
        "core_meaning": "Tin nhắn chưa rõ nên mình còn đoán ý.",
        "reader_takeaway": "Hỏi lại đúng chỗ chưa rõ.",
        "scene_status": "illustrative",
        "scene_anchors": ["tin nhắn"],
        "action_anchors": ["hỏi"],
    }
    payload = _daily_payload() | {"meaning_brief": brief}
    safe = PrivacyMinimiser().minimise(RewriteSurface.DAILY_HOME, payload)
    assert safe["meaning_brief"] == brief
    question_brief = brief | {"observation_question": "Sau khi hỏi lại, bạn đã hiểu tin nhắn chưa?"}
    assert (
        PrivacyMinimiser().minimise(
            RewriteSurface.DAILY_HOME, payload | {"meaning_brief": question_brief}
        )["meaning_brief"]
        == question_brief
    )
    for invalid in (
        brief | {"birth_date": "1990-03-15"},
        brief | {"core_meaning": "Nhắn an@example.com để hỏi."},
        brief | {"scene_status": "observed"},
        brief | {"observation_question": "Bạn đã nhắn an@example.com chưa?"},
    ):
        with pytest.raises(UnsafeRewritePayload):
            PrivacyMinimiser().minimise(
                RewriteSurface.DAILY_HOME, payload | {"meaning_brief": invalid}
            )


@pytest.mark.parametrize(
    "question",
    [
        "Nhắn cho mình qua an@example.com nhé",
        "Sinh ngày 1990-03-15 thì có hợp không?",
        "Gọi số 0912345678 để hỏi tiếp",
    ],
)
def test_tarot_question_with_direct_identifier_skips_external_generation(question: str) -> None:
    assert reduce_tarot_question(question, category="relationship") is None


def test_radar_payload_accepts_only_derived_dimensions_and_anonymous_evidence() -> None:
    payload = {
        "context": "crush",
        "low_signal": False,
        "dimensions": [
            {
                "dimension": "coordination",
                "band": "medium",
                "direction": "mixed",
                "meaning_keys": ["different_response_speed"],
            }
        ],
        "source_sections": [
            {"key": "overview", "meaning": "Hai người dễ chú ý đến nhau."},
            {"key": "strength", "meaning": "Cách nói chuyện có thể vào nhịp nhanh."},
            {"key": "friction", "meaning": "Tốc độ phản hồi khác nhau dễ gây hiểu nhầm."},
            {"key": "asymmetry", "meaning": "Hai phía có thể cảm nhận khác nhau."},
            {"key": "prompt", "meaning": "Hỏi rõ một câu thay vì đoán ý."},
        ],
        "evidence": [
            {
                "label": "signal_1",
                "source": "relationship",
                "kind": "synastry_aspect",
                "domain": "communication",
                "role": "friction",
                "confidence": "medium",
                "labels": [{"name": "aspect", "value": "vuông"}],
            }
        ],
    }

    safe = PrivacyMinimiser().minimise(RewriteSurface.RADAR, payload)
    assert safe == payload

    with pytest.raises(UnsafeRewritePayload):
        PrivacyMinimiser().minimise(
            RewriteSurface.RADAR,
            {**payload, "other_person_name": "Bình"},
        )
