import sqlite3
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"


def _client(path: Path) -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{path}",
            cors_origins=[cast(Any, ORIGIN)],
            guest_cookie_secure=False,
        )
    )
    return TestClient(app, base_url=ORIGIN)


def _full_profile(client: TestClient, key: str, birth_date: str, birth_time: str) -> str:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": key,
        },
    )
    assert guest.status_code == 200
    csrf = guest.json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    assert (
        client.post(
            "/v1/birth-profile", headers=headers, json={"birth_date": birth_date}
        ).status_code
        == 200
    )
    supplement = client.post(
        "/v1/birth-profile/supplement",
        headers=headers,
        json={
            "birth_time_mode": "exact",
            "birth_time_local": birth_time,
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        },
    )
    assert supplement.status_code == 200
    assert supplement.json()["profile_level"] == 3
    return str(csrf)


def _assert_dossier_payload(payload: dict[str, Any]) -> None:
    assert payload["version"] == "radar-result-v2"
    assert len(payload["compatibility_map"]) == 3
    sections = payload["sections"]
    assert isinstance(sections, list) and len(sections) == 4
    assert [section["key"] for section in sections] == [
        "fit",
        "friction",
        "perspective",
        "check",
    ]
    assert all("topics" in section and "highlights" in section for section in sections)
    metadata = payload["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["renderer_version"] == "radar-living-dossier-v1"


def _assert_no_raw_birth_data(payload: object) -> None:
    forbidden_keys = {
        "birth_date",
        "birth_time",
        "birth_time_local",
        "place_id",
        "latitude",
        "longitude",
        "timezone_id",
    }
    forbidden_values = {
        "1994-03-12",
        "1996-07-21",
        "08:15",
        "19:40",
        "vn-hanoi",
        "vn-dak-lak",
        "21.0285",
        "105.8542",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)
        elif isinstance(value, str):
            assert value not in forbidden_values

    walk(payload)


def test_private_radar_requires_both_people_and_supports_withdrawal(tmp_path: Path) -> None:
    database = tmp_path / "radar.db"
    with _client(database) as owner:
        owner_csrf = _full_profile(owner, "radar-owner-guest-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": owner_csrf}
        assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
        created = owner.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Mèo", "context": "crush"},
        )
        assert created.status_code == 200
        assert created.json()["mode"] == "consented_invite"
        request_id = created.json()["id"]
        token = created.json()["share_url"].rsplit("/", 1)[-1]

        recipient = TestClient(owner.app, base_url=ORIGIN)
        preview = recipient.get(f"/v1/public/radar/{token}")
        assert preview.status_code == 200
        assert preview.json()["request_id"] == request_id
        assert preview.headers["cache-control"].startswith("no-store")
        assert preview.headers["referrer-policy"] == "no-referrer"
        assert preview.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        assert "birth_date" not in preview.text
        assert "birth_time" not in preview.text
        assert "latitude" not in preview.text

        no_profile = recipient.post(
            "/v1/public/radar/current/accept",
            headers={"Origin": ORIGIN},
            json={"request_id": request_id, "consent_version": "radar-pair-v1"},
        )
        assert no_profile.status_code == 401
        recipient_csrf = _full_profile(
            recipient, "radar-recipient-guest-1234567", "1996-07-21", "19:40"
        )
        result = recipient.post(
            "/v1/public/radar/current/accept",
            headers={"Origin": ORIGIN, "X-CSRF-Token": recipient_csrf},
            json={"request_id": request_id, "consent_version": "radar-pair-v1"},
        )
        assert result.status_code == 200
        assert result.json()["mode"] == "consented_invite"
        _assert_dossier_payload(result.json())
        _assert_no_raw_birth_data(result.json())
        assert "score" not in result.text.lower()
        assert "1996-07-21" not in result.text
        assert "19:40" not in result.text
        assert "vn-hanoi" not in result.text
        assert recipient.get(f"/v1/public/radar/{token}").status_code == 404
        receipt_result = recipient.get("/v1/public/radar/receipt")
        assert receipt_result.status_code == 200
        assert receipt_result.json()["request_id"] == request_id
        assert receipt_result.json()["mode"] == "consented_invite"
        _assert_dossier_payload(receipt_result.json())
        _assert_no_raw_birth_data(receipt_result.json())

        owner_result = owner.get(f"/v1/radar/results/{request_id}")
        assert owner_result.status_code == 200
        _assert_dossier_payload(owner_result.json())
        _assert_no_raw_birth_data(owner_result.json())
        assert (
            owner_result.json()["sections"][2]["perspectives"][0]["body"]
            != result.json()["sections"][2]["perspectives"][0]["body"]
        )
        assert "birth_date" not in owner_result.text
        assert "latitude" not in owner_result.text
        with sqlite3.connect(database) as connection:
            label, result_ciphertext = connection.execute(
                "SELECT recipient_label_ciphertext, result_ciphertext FROM radar_requests"
            ).fetchone()
        assert label.startswith("aesgcm:") and "Mèo" not in label
        assert result_ciphertext.startswith("aesgcm:")
        assert result.json()["headline"] not in result_ciphertext

        withdrawn = recipient.post(
            "/v1/public/radar/receipt/withdraw",
            headers={"Origin": ORIGIN},
            json={"request_id": request_id},
        )
        assert withdrawn.status_code == 204
        assert recipient.get("/v1/public/radar/receipt").status_code == 404
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 404


def test_private_check_computes_without_persisting_other_person_birth_input(
    tmp_path: Path,
) -> None:
    database = tmp_path / "radar-private-check.db"
    with _client(database) as owner:
        owner_csrf = _full_profile(owner, "radar-private-owner-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": owner_csrf}
        assert owner.post("/v1/identity/claim", headers=headers).status_code == 200

        response = owner.post(
            "/v1/radar/private-checks",
            headers=headers,
            json={
                "recipient_label": "Người hay seen",
                "context": "crush",
                "birth_date": "1996-07-21",
                "birth_time_local": "19:40",
                "place_id": "vn-dak-lak",
                "consent_version": "radar-authorized-input-v1",
                "authorization_attested": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["request_id"]
        assert payload["mode"] == "private_check"
        _assert_dossier_payload(payload)
        _assert_no_raw_birth_data(payload)
        assert "score" not in response.text.lower()
        assert "1996-07-21" not in response.text
        assert "19:40" not in response.text
        assert "vn-dak-lak" not in response.text

        with sqlite3.connect(database) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(radar_requests)")}
            row = connection.execute(
                "SELECT mode, consent_version, authorization_attested_at, token_hash, "
                "recipient_label_ciphertext, result_ciphertext FROM radar_requests"
            ).fetchone()
        assert {"birth_date", "birth_time_local", "place_id"}.isdisjoint(columns)
        assert row[0:2] == ("private_check", "radar-authorized-input-v1")
        assert row[2] is not None and row[3] is None
        assert row[4].startswith("aesgcm:") and "Người hay seen" not in row[4]
        assert row[5].startswith("aesgcm:")
        assert payload["headline"] not in row[5]

        request_id = payload["request_id"]
        stored = owner.get(f"/v1/radar/results/{request_id}")
        assert stored.status_code == 200
        assert stored.json()["mode"] == "private_check"
        _assert_dossier_payload(stored.json())
        _assert_no_raw_birth_data(stored.json())
        assert stored.json()["sections"][0]["highlights"] == payload["sections"][0]["highlights"]
        assert owner.delete(f"/v1/radar/results/{request_id}", headers=headers).status_code == 204
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 404


def test_private_check_requires_permission_and_valid_adult_birth_input(tmp_path: Path) -> None:
    with _client(tmp_path / "radar-private-invalid.db") as owner:
        csrf = _full_profile(owner, "radar-private-invalid-1234567", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        owner.post("/v1/identity/claim", headers=headers)
        base = {
            "recipient_label": "Bạn",
            "context": "friend",
            "birth_date": "1996-07-21",
            "birth_time_local": "19:40",
            "place_id": "vn-hanoi",
            "consent_version": "radar-authorized-input-v1",
            "authorization_attested": False,
        }
        assert owner.post("/v1/radar/private-checks", headers=headers, json=base).status_code == 422
        assert (
            owner.post(
                "/v1/radar/private-checks",
                headers=headers,
                json={**base, "authorization_attested": True, "birth_date": "2012-07-21"},
            ).status_code
            == 422
        )
        assert (
            owner.post(
                "/v1/radar/private-checks",
                headers=headers,
                json={**base, "authorization_attested": True, "place_id": "unknown"},
            ).status_code
            == 422
        )


def test_owner_cannot_create_radar_without_exact_chart(tmp_path: Path) -> None:
    with _client(tmp_path / "radar-missing.db") as owner:
        guest = owner.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "radar-missing-chart-guest-12345",
            },
        )
        csrf = guest.json()["csrf_token"]
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        owner.post("/v1/birth-profile", headers=headers, json={"birth_date": "1990-01-01"})
        owner.post("/v1/identity/claim", headers=headers)

        response = owner.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Bạn", "context": "friend"},
        )

        assert response.status_code == 409


def test_invite_actions_reject_stale_request_bindings(tmp_path: Path) -> None:
    with _client(tmp_path / "radar-stale-binding.db") as owner:
        owner_csrf = _full_profile(owner, "radar-stale-owner-123456789", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": owner_csrf}
        assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
        first = owner.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Một", "context": "friend"},
        ).json()
        second = owner.post(
            "/v1/radar/requests",
            headers=headers,
            json={"recipient_label": "Hai", "context": "friend"},
        ).json()

        recipient = TestClient(owner.app, base_url=ORIGIN)
        recipient_csrf = _full_profile(
            recipient, "radar-stale-recipient-123456", "1996-07-21", "19:40"
        )
        recipient_headers = {"Origin": ORIGIN, "X-CSRF-Token": recipient_csrf}
        first_token = first["share_url"].rsplit("/", 1)[-1]
        second_token = second["share_url"].rsplit("/", 1)[-1]

        assert recipient.get(f"/v1/public/radar/{first_token}").status_code == 200
        assert recipient.get(f"/v1/public/radar/{second_token}").status_code == 200
        stale_accept = recipient.post(
            "/v1/public/radar/current/accept",
            headers=recipient_headers,
            json={"request_id": first["id"], "consent_version": "radar-pair-v1"},
        )
        assert stale_accept.status_code == 422

        accepted_second = recipient.post(
            "/v1/public/radar/current/accept",
            headers=recipient_headers,
            json={"request_id": second["id"], "consent_version": "radar-pair-v1"},
        )
        assert accepted_second.status_code == 200
        assert recipient.get(f"/v1/public/radar/{first_token}").status_code == 200
        accepted_first = recipient.post(
            "/v1/public/radar/current/accept",
            headers=recipient_headers,
            json={"request_id": first["id"], "consent_version": "radar-pair-v1"},
        )
        assert accepted_first.status_code == 200

        stale_withdraw = recipient.post(
            "/v1/public/radar/receipt/withdraw",
            headers={"Origin": ORIGIN},
            json={"request_id": second["id"]},
        )
        assert stale_withdraw.status_code == 404
        assert owner.get(f"/v1/radar/results/{second['id']}").status_code == 200
        assert (
            recipient.post(
                "/v1/public/radar/receipt/withdraw",
                headers={"Origin": ORIGIN},
                json={"request_id": first["id"]},
            ).status_code
            == 204
        )


def test_expired_private_result_is_not_reopened(tmp_path: Path) -> None:
    database = tmp_path / "radar-expired-result.db"
    with _client(database) as owner:
        csrf = _full_profile(owner, "radar-expired-result-123456", "1994-03-12", "08:15")
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
        created = owner.post(
            "/v1/radar/private-checks",
            headers=headers,
            json={
                "recipient_label": "Bản cũ",
                "context": "friend",
                "birth_date": "1996-07-21",
                "birth_time_local": "19:40",
                "place_id": "vn-hanoi",
                "consent_version": "radar-authorized-input-v1",
                "authorization_attested": True,
            },
        )
        assert created.status_code == 200
        request_id = created.json()["request_id"]
        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE radar_requests SET expires_at = '2020-01-01 00:00:00'",
            )
            connection.commit()
        assert owner.get(f"/v1/radar/results/{request_id}").status_code == 404
