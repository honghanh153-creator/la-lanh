import json
from uuid import uuid4

from app.domains.share.models import SafeShareSnapshot
from app.domains.share.rewrite import (
    RecordedRecapActivity,
    compile_recap_rewrite_request,
    compile_share_rewrite_request,
    rewrite_recap,
    rewrite_share_snapshot,
)
from app.infrastructure.generation.privacy import PrivacyMinimiser


def _snapshot() -> SafeShareSnapshot:
    return SafeShareSnapshot(
        title="Chưa rõ thì chưa cần kết luận.",
        body="Một tin nhắn ngắn chưa đủ để biết người kia đang nghĩ gì.",
        context_label="Aura · bản đọc tổng hòa",
        content_version="daily-v4",
        persona_mode="aura",
        persona_label="Mềm",
        persona_version="persona-v2",
        watermark="Lá Lành",
    )


def test_share_compiler_exposes_only_the_frozen_public_snapshot() -> None:
    guest_id = uuid4()
    artifact_id = uuid4()
    request = compile_share_rewrite_request(
        guest_id,
        artifact_id,
        _snapshot(),
        model_version="gpt-6-luna",
        prompt_version="share-rewrite-v1",
    )

    safe = PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    serialized = json.dumps(safe, ensure_ascii=False)
    assert str(guest_id) not in serialized
    assert str(artifact_id) not in serialized
    assert "birth" not in serialized.casefold()
    assert set(safe) == {
        "source_headline",
        "source_summary",
        "approved_claim_keys",
        "activity_keys",
        "activity_summaries",
    }


def test_share_rewrite_preserves_snapshot_metadata_and_rejects_new_private_claims() -> None:
    baseline = _snapshot()
    candidate = rewrite_share_snapshot(
        baseline,
        {
            "headline": "Chưa rõ thì khoan kết luận.",
            "summary": "Một tin nhắn ngắn vẫn chưa đủ để biết người kia nghĩ gì.",
        },
    )

    assert candidate is not None
    assert candidate.content_version == baseline.content_version
    assert candidate.watermark == baseline.watermark
    assert (
        rewrite_share_snapshot(
            baseline,
            {
                "headline": "Ngày sinh nói rằng hai người là định mệnh.",
                "summary": baseline.body,
            },
        )
        is None
    )


def test_recap_can_only_summarize_recorded_activity() -> None:
    guest_id = uuid4()
    activities = (
        RecordedRecapActivity("note.opened", "Bạn đã mở Note hôm nay ba lần trong tuần."),
        RecordedRecapActivity("tarot.completed", "Bạn đã hoàn thành một trải bài ba lá."),
    )
    request = compile_recap_rewrite_request(
        guest_id,
        "2026-W40",
        activities,
        model_version="gpt-6-luna",
        prompt_version="recap-rewrite-v1",
    )

    assert request is not None
    safe = PrivacyMinimiser().minimise(request.key.surface, request.safe_payload)
    assert safe["activity_keys"] == ["note.opened", "tarot.completed"]

    recap = rewrite_recap(
        activities,
        {
            "headline": "Một tuần có Note và Tarot.",
            "summary": "Bạn đã mở Note hôm nay và hoàn thành một trải bài ba lá.",
        },
    )
    assert recap is not None
    assert recap.activity_keys == ("note.opened", "tarot.completed")

    invented = rewrite_recap(
        activities,
        {
            "headline": "Bạn đã match thành công.",
            "summary": "Tuần này bạn đã gặp một người mới và có một cuộc hẹn.",
        },
    )
    assert invented is None
