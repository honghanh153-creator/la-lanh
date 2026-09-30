from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.domains.astro.models import DateOnlySunResult, EngineProvenance, ZodiacSign
from app.domains.content.models import canonical_payload_hash
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.main import create_app


@contextmanager
def _client(tmp_path: Path, *, enabled: bool) -> Iterator[TestClient]:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'studio.db'}",
        content_studio_enabled=enabled,
        content_studio_api_token="s" * 32 if enabled else None,
    )
    with TestClient(create_app(settings)) as client:
        yield client


def test_studio_routes_are_absent_when_disabled(tmp_path: Path) -> None:
    with _client(tmp_path, enabled=False) as client:
        response = client.get("/v1/studio/workspace")
        schema = client.get("/openapi.json").json()

    assert response.status_code == 404
    assert "/v1/studio/workspace" not in schema["paths"]


def test_content_studio_configuration_requires_a_token() -> None:
    with pytest.raises(ValidationError, match="requires an API token"):
        Settings(content_studio_enabled=True)


def test_content_studio_configuration_rejects_a_short_token() -> None:
    too_short = "x" * 5
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(content_studio_enabled=True, content_studio_api_token=too_short)


def test_content_studio_configuration_rejects_production_beta_auth() -> None:
    with pytest.raises(ValidationError, match="not approved outside local development"):
        Settings(
            environment="production",
            content_studio_enabled=True,
            content_studio_api_token="s" * 32,
        )


def test_content_studio_configuration_rejects_staging_beta_auth() -> None:
    with pytest.raises(ValidationError, match="not approved outside local development"):
        Settings(
            environment="staging",
            content_studio_enabled=True,
            content_studio_api_token="s" * 32,
        )


def test_workspace_requires_token_and_returns_no_store(tmp_path: Path) -> None:
    with _client(tmp_path, enabled=True) as client:
        denied = client.get("/v1/studio/workspace")
        allowed = client.get(
            "/v1/studio/workspace",
            headers={"Authorization": f"Bearer {'s' * 32}"},
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert allowed.headers["cache-control"] == "no-store, max-age=0"
    assert allowed.json()["source"] == "bundled-baseline"
    assert allowed.json()["summary"]["signs"] == 12


def test_studio_auth_and_body_limits_run_before_request_parsing(tmp_path: Path) -> None:
    auth = {"Authorization": f"Bearer {'s' * 32}"}
    with _client(tmp_path, enabled=True) as client:
        unauthenticated = client.post(
            "/v1/studio/drafts",
            content=b"{",
            headers={"Content-Type": "application/json"},
        )
        oversized = client.post(
            "/v1/studio/drafts",
            content=b"x" * 262_145,
            headers={**auth, "Content-Type": "application/json"},
        )
        chunked_oversized = client.post(
            "/v1/studio/drafts",
            content=iter((b"x" * 131_073, b"y" * 131_073)),
            headers={**auth, "Content-Type": "application/json"},
        )

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "STUDIO_UNAUTHORIZED"
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "STUDIO_BODY_TOO_LARGE"
    assert chunked_oversized.status_code == 413
    assert chunked_oversized.json()["code"] == "STUDIO_BODY_TOO_LARGE"


def test_publish_changes_new_rendering_and_preserves_release_identity(tmp_path: Path) -> None:
    auth = {"Authorization": f"Bearer {'s' * 32}"}
    with _client(tmp_path, enabled=True) as client:
        workspace = client.get("/v1/studio/workspace", headers=auth).json()
        payload = workspace["payload"]
        payload["signs"]["pisces"]["hooks"] = [
            "Bạn đang tự nối thêm ý nghĩa cho một câu trả lời ngắn hơn thường lệ.",
            "Bạn đang tự nối thêm ý nghĩa khi không khí quanh mình đổi khác.",
            "Bạn đang tự nối thêm ý nghĩa trước khi có đủ dữ kiện để kết luận.",
        ]
        draft = client.post(
            "/v1/studio/drafts",
            headers={**auth, "Idempotency-Key": "draft-runtime-test"},
            json={
                "payload": payload,
                "parent_revision_id": None,
                "reason": "Kiểm tra release đi vào engine thật",
            },
        )
        assert draft.status_code == 201
        draft_body = draft.json()
        assert draft_body["validation"]["passed"] is True

        published = client.post(
            f"/v1/studio/revisions/{draft_body['revision']['id']}/publish",
            headers={**auth, "Idempotency-Key": "publish-runtime-test"},
            json={
                "expected_generation": workspace["channel"]["generation"],
                "reason": "Duyệt nội dung cho local review",
            },
        )
        assert published.status_code == 200

        plan = ReadingPlanner().plan(
            DateOnlySunResult(
                status="certain",
                sign=ZodiacSign.PISCES,
                candidates=(ZodiacSign.PISCES,),
                provenance=EngineProvenance(version="2.10.03", profile="test"),
            ),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-09-12",
        )
        candidate = DeterministicVietnameseRenderer().render(plan)

        assert candidate.renderer_version == (
            f"deterministic-vi-v6+content-{canonical_payload_hash(payload)[:12]}"
        )
        assert "tự nối thêm ý nghĩa" in candidate.hook


def test_failed_draft_cannot_advance_the_active_channel(tmp_path: Path) -> None:
    auth = {"Authorization": f"Bearer {'s' * 32}"}
    with _client(tmp_path, enabled=True) as client:
        workspace = client.get("/v1/studio/workspace", headers=auth).json()
        payload = workspace["payload"]
        payload["signs"]["pisces"]["hooks"] = "Sai kiểu dữ liệu dù câu đủ dài."
        draft = client.post(
            "/v1/studio/drafts",
            headers={**auth, "Idempotency-Key": "draft-invalid-shape"},
            json={"payload": payload, "reason": "Kiểm tra gate chặn field sai kiểu"},
        )

        assert draft.status_code == 422
        draft_body = draft.json()
        assert draft_body["validation"]["passed"] is False
        after = client.get("/v1/studio/workspace", headers=auth).json()

        assert after["channel"]["generation"] == 0
        assert after["channel"]["active_revision_id"] is None
        assert after["revisions"] == []
        assert all(event["action"] != "published" for event in after["events"])


def test_rollback_restores_a_previously_published_catalog(tmp_path: Path) -> None:
    auth = {"Authorization": f"Bearer {'s' * 32}"}
    with _client(tmp_path, enabled=True) as client:
        workspace = client.get("/v1/studio/workspace", headers=auth).json()
        payload_a = workspace["payload"]
        payload_a["signs"]["pisces"]["hooks"] = [
            "Bản A mở bằng một tình huống có thể nhận ra ngay.",
            "Bản A hỏi thẳng trước khi tự nối thêm ý nghĩa.",
            "Bản A giữ dữ kiện thật ở phía trước suy đoán.",
        ]
        draft_a = client.post(
            "/v1/studio/drafts",
            headers={**auth, "Idempotency-Key": "draft-a"},
            json={"payload": payload_a, "reason": "Tạo release A"},
        ).json()
        release_a_id = draft_a["revision"]["id"]
        assert (
            client.post(
                f"/v1/studio/revisions/{release_a_id}/publish",
                headers={**auth, "Idempotency-Key": "publish-a"},
                json={"expected_generation": 0, "reason": "Publish release A"},
            ).status_code
            == 200
        )

        workspace_a = client.get("/v1/studio/workspace", headers=auth).json()
        payload_b = workspace_a["payload"]
        payload_b["signs"]["pisces"]["hooks"] = [
            "Bản B dùng một câu mở khác để kiểm tra rollback.",
            "Bản B giữ một biến thể thứ hai thật dễ phân biệt.",
            "Bản B giữ một biến thể thứ ba thật dễ phân biệt.",
        ]
        draft_b = client.post(
            "/v1/studio/drafts",
            headers={**auth, "Idempotency-Key": "draft-b"},
            json={
                "payload": payload_b,
                "parent_revision_id": release_a_id,
                "reason": "Tạo release B",
            },
        ).json()
        release_b_id = draft_b["revision"]["id"]
        assert (
            client.post(
                f"/v1/studio/revisions/{release_b_id}/publish",
                headers={**auth, "Idempotency-Key": "publish-b"},
                json={"expected_generation": 1, "reason": "Publish release B"},
            ).status_code
            == 200
        )

        rollback = client.post(
            f"/v1/studio/revisions/{release_a_id}/rollback",
            headers={**auth, "Idempotency-Key": "rollback-a"},
            json={"expected_generation": 2, "reason": "Quay lại release A"},
        )
        after = client.get("/v1/studio/workspace", headers=auth).json()

        assert rollback.status_code == 200
        assert after["channel"]["active_revision_id"] == release_a_id
        assert after["channel"]["generation"] == 3
        rollback_event = next(
            event for event in after["events"] if event["action"] == "rolled_back"
        )
        assert rollback_event["previous_revision_id"] == release_b_id


def test_startup_restores_the_persisted_active_catalog(tmp_path: Path) -> None:
    auth = {"Authorization": f"Bearer {'s' * 32}"}
    payload_hash = ""
    with _client(tmp_path, enabled=True) as first_client:
        workspace = first_client.get("/v1/studio/workspace", headers=auth).json()
        payload = workspace["payload"]
        payload["signs"]["pisces"]["hooks"] = [
            "Sau restart, câu mở này vẫn phải đến từ release đã duyệt.",
            "Sau restart, biến thể thứ hai vẫn phải đến từ release đã duyệt.",
            "Sau restart, biến thể thứ ba vẫn phải đến từ release đã duyệt.",
        ]
        payload_hash = canonical_payload_hash(payload)
        draft = first_client.post(
            "/v1/studio/drafts",
            headers={**auth, "Idempotency-Key": "draft-restart"},
            json={"payload": payload, "reason": "Kiểm tra startup restore"},
        ).json()
        assert (
            first_client.post(
                f"/v1/studio/revisions/{draft['revision']['id']}/publish",
                headers={**auth, "Idempotency-Key": "publish-restart"},
                json={"expected_generation": 0, "reason": "Publish trước restart"},
            ).status_code
            == 200
        )

    with _client(tmp_path, enabled=True):
        plan = ReadingPlanner().plan(
            DateOnlySunResult(
                status="certain",
                sign=ZodiacSign.PISCES,
                candidates=(ZodiacSign.PISCES,),
                provenance=EngineProvenance(version="2.10.03", profile="test"),
            ),
            purpose=ReadingPurpose.DAILY_NOTE,
            editorial_seed="2026-09-12",
        )
        candidate = DeterministicVietnameseRenderer().render(plan)

        assert "Sau restart" in candidate.hook
        assert candidate.renderer_version == f"deterministic-vi-v6+content-{payload_hash[:12]}"
