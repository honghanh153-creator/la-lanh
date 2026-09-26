import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _owner_client(tmp_path: Path) -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'la-chung.db'}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    return TestClient(app, base_url="http://127.0.0.1:5173")


def test_anonymous_recipient_flow_is_real_idempotent_and_withdrawable(tmp_path: Path) -> None:
    with _owner_client(tmp_path) as owner:
        guest = owner.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "la-chung-guest-123456789",
            },
        )
        claim = owner.post(
            "/v1/identity/claim",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
        )
        assert claim.status_code == 200

        invite_payload = {
            "recipient_label": "một người bạn",
            "context": "bff",
            "idempotency_key": "invite-create-idempotency-123456",
        }
        rejected = owner.post(
            "/v1/la-chung/requests",
            json=invite_payload,
        )
        assert rejected.status_code == 403
        mutation_headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        created = owner.post(
            "/v1/la-chung/requests",
            headers=mutation_headers,
            json=invite_payload,
        )
        assert created.status_code == 200
        replayed_create = owner.post(
            "/v1/la-chung/requests",
            headers=mutation_headers,
            json=invite_payload,
        )
        assert replayed_create.status_code == 200
        assert replayed_create.json()["id"] == created.json()["id"]
        assert replayed_create.json()["share_url"] == created.json()["share_url"]
        with sqlite3.connect(tmp_path / "la-chung.db") as connection:
            request_count, plaintext_label, ciphertext_label, idempotency_hash, draft_hash = (
                connection.execute(
                    "SELECT COUNT(*), recipient_label, recipient_label_ciphertext, "
                    "idempotency_hash, draft_hash FROM la_chung_requests"
                ).fetchone()
            )
        assert request_count == 1
        assert plaintext_label is None
        assert ciphertext_label.startswith("aesgcm:")
        assert "một người bạn" not in ciphertext_label
        assert len(idempotency_hash) == len(draft_hash) == 32
        request_id = created.json()["id"]
        share_url = created.json()["share_url"]
        token = share_url.rsplit("/", 1)[-1]

        recipient = TestClient(owner.app, base_url="http://127.0.0.1:5173")
        preview = recipient.get(f"/v1/public/la-chung/{token}")
        assert preview.status_code == 200
        assert preview.headers["cache-control"].startswith("no-store")
        assert preview.headers["referrer-policy"] == "no-referrer"
        assert preview.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        statement_ids = [item["id"] for item in preview.json()["statements"][:3]]
        reported = recipient.post(
            f"/v1/public/la-chung/{token}/report",
            json={"reason": "not_for_me"},
        )
        assert reported.status_code == 202
        duplicate_report = recipient.post(
            f"/v1/public/la-chung/{token}/report",
            json={"reason": "not_for_me"},
        )
        assert duplicate_report.status_code == 202
        with sqlite3.connect(tmp_path / "la-chung.db") as connection:
            assert connection.execute("SELECT COUNT(*) FROM la_chung_reports").fetchone()[0] == 1
        payload = {
            "statement_ids": statement_ids,
            "identity_mode": "anonymous",
            "display_alias": "must not be stored",
            "idempotency_key": "response-idempotency-123456",
        }
        submitted = recipient.post(f"/v1/public/la-chung/{token}/responses", json=payload)
        replayed = recipient.post(f"/v1/public/la-chung/{token}/responses", json=payload)
        assert submitted.status_code == replayed.status_code == 200
        assert submitted.json()["request_id"] == replayed.json()["request_id"]
        assert replayed.json()["resumed"] is True
        terminal_preview = recipient.get(f"/v1/public/la-chung/{token}")
        assert terminal_preview.status_code == 404
        assert terminal_preview.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        assert (
            recipient.post(
                f"/v1/public/la-chung/{token}/report",
                json={"reason": "spam"},
            ).status_code
            == 202
        )
        with sqlite3.connect(tmp_path / "la-chung.db") as connection:
            assert connection.execute("SELECT COUNT(*) FROM la_chung_reports").fetchone()[0] == 1

        result = owner.get(f"/v1/la-chung/results/{request_id}")
        assert result.status_code == 200
        assert result.json()["identity_mode"] == "anonymous"
        assert result.json()["display_alias"] is None
        assert "ip" not in result.json()
        assert "device" not in result.json()

        hidden = owner.post(
            f"/v1/la-chung/results/{request_id}/hide",
            headers=mutation_headers,
        )
        assert hidden.status_code == 204
        assert owner.get(f"/v1/la-chung/results/{request_id}").status_code == 404

        withdrawn = recipient.post("/v1/public/la-chung/receipt/withdraw")
        assert withdrawn.status_code == 204
        assert owner.get(f"/v1/la-chung/results/{request_id}").status_code == 404
        deleted = owner.delete(
            f"/v1/la-chung/results/{request_id}",
            headers=mutation_headers,
        )
        assert deleted.status_code == 204
        assert request_id not in {item["id"] for item in owner.get("/v1/la-chung/requests").json()}

    with sqlite3.connect(tmp_path / "la-chung.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM la_chung_reports").fetchone()[0] == 0


def test_selection_and_alias_validation_fail_closed(tmp_path: Path) -> None:
    with _owner_client(tmp_path) as owner:
        guest = owner.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "la-chung-validation-123456",
            },
        )
        owner.post(
            "/v1/identity/claim",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
        )
        created = owner.post(
            "/v1/la-chung/requests",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
            json={
                "recipient_label": "crush",
                "context": "crush",
                "idempotency_key": "invite-replacement-idempotency-123456",
            },
        )
        old_token = created.json()["share_url"].rsplit("/", 1)[-1]
        replacement = owner.post(
            f"/v1/la-chung/requests/{created.json()['id']}/replacement",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
        )
        assert replacement.status_code == 200
        token = replacement.json()["share_url"].rsplit("/", 1)[-1]
        assert token != old_token
        assert owner.get(f"/v1/public/la-chung/{old_token}").status_code == 404
        assert owner.get(f"/v1/public/la-chung/{token}").status_code == 200
        invalid = owner.post(
            f"/v1/public/la-chung/{token}/responses",
            json={
                "statement_ids": ["warm-presence", "warm-presence", "unknown"],
                "identity_mode": "alias",
                "display_alias": "0901234567",
                "idempotency_key": "invalid-response-12345678",
            },
        )
        assert invalid.status_code == 404


def test_idempotency_is_bound_to_capability_and_receipt_expires_server_side(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "la-chung.db"
    with _owner_client(tmp_path) as owner:
        guest = owner.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "la-chung-bound-idem-123456",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        owner.post("/v1/identity/claim", headers=headers)
        tokens = []
        for index, label in enumerate(("bạn một", "bạn hai"), start=1):
            created = owner.post(
                "/v1/la-chung/requests",
                headers=headers,
                json={
                    "recipient_label": label,
                    "context": "friend",
                    "idempotency_key": f"invite-bound-idempotency-{index}-123456",
                },
            )
            tokens.append(created.json()["share_url"].rsplit("/", 1)[-1])

        recipient = TestClient(owner.app, base_url="http://127.0.0.1:5173")
        statement_ids = [
            item["id"]
            for item in recipient.get(f"/v1/public/la-chung/{tokens[0]}").json()["statements"][:3]
        ]
        payload = {
            "statement_ids": statement_ids,
            "identity_mode": "anonymous",
            "idempotency_key": "same-client-idempotency-123456",
        }
        first = recipient.post(f"/v1/public/la-chung/{tokens[0]}/responses", json=payload)
        second = recipient.post(f"/v1/public/la-chung/{tokens[1]}/responses", json=payload)
        assert first.status_code == second.status_code == 200
        assert first.json()["request_id"] != second.json()["request_id"]

        expired_at = (datetime.now(UTC) - timedelta(days=8)).isoformat()
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                "UPDATE la_chung_responses SET submitted_at = ?",
                (expired_at,),
            )
            connection.commit()
        failed_withdraw = recipient.post("/v1/public/la-chung/receipt/withdraw")
        assert failed_withdraw.status_code == 404
        assert failed_withdraw.headers["x-robots-tag"] == "noindex, nofollow, noarchive"


def test_owner_result_has_a_typed_openapi_response(tmp_path: Path) -> None:
    with _owner_client(tmp_path) as client:
        document = client.get("/openapi.json").json()

    schema = document["components"]["schemas"]["OwnerResultResponse"]
    assert set(schema["required"]) == {
        "request_id",
        "recipient_label",
        "identity_mode",
        "display_alias",
        "statements",
        "submitted_at",
    }
    success = document["paths"]["/v1/la-chung/results/{request_id}"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert success["$ref"] == "#/components/schemas/OwnerResultResponse"
