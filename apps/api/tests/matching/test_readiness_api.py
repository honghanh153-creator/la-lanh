import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url=f"sqlite+aiosqlite:///{tmp_path / 'matching.db'}",
                cors_origins=[ORIGIN],
                guest_cookie_secure=False,
            )
        ),
        base_url=ORIGIN,
    )


def _guest_with_birth(client: TestClient) -> str:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "matching-readiness-guest-123456789",
        },
    )
    assert guest.status_code == 200
    csrf = guest.json()["csrf_token"]
    birth = client.post(
        "/v1/birth-profile",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        json={"birth_date": "1994-04-21"},
    )
    assert birth.status_code == 200
    return str(csrf)


def test_matching_requires_owner_only_when_user_enters_feature(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        csrf = _guest_with_birth(client)

        guest_readiness = client.get("/v1/matching/readiness")
        assert guest_readiness.status_code == 401
        assert guest_readiness.json()["code"] == "OWNER_REQUIRED"

        claim = client.post(
            "/v1/identity/claim",
            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
        )
        assert claim.status_code == 200

        readiness = client.get("/v1/matching/readiness")
        assert readiness.status_code == 200
        payload = readiness.json()
        assert payload["ready"] is False
        assert payload["birth_profile_level"] == 1
        assert payload["verification_status"] == "not_started"
        assert {item["key"] for item in payload["checks"]} == {
            "age_18_plus",
            "birth_profile_level_3",
            "matching_profile",
            "matching_consent",
            "photo_verification",
        }


def test_matching_profile_and_consent_are_explicit_and_pool_fails_closed(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        csrf = _guest_with_birth(client)
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert client.post("/v1/identity/claim", headers=headers).status_code == 200

        profile = client.put(
            "/v1/matching/profile",
            headers=headers,
            json={
                "display_name": "An",
                "gender_identity": "nonbinary",
                "intent": "open",
                "gender_preference": "everyone",
                "min_age": 24,
                "max_age": 36,
                "region_code": "ho-chi-minh",
                "weekly_intent": "de_la_can",
            },
        )
        assert profile.status_code == 200
        assert profile.json()["active"] is False
        with sqlite3.connect(tmp_path / "matching.db") as database:
            stored_display_name = database.execute(
                "SELECT display_name_ciphertext FROM matching_profiles"
            ).fetchone()[0]
        assert stored_display_name != "An"
        # Ciphertext is randomized binary encoded as URL-safe text; a two-character
        # plaintext can appear by chance in that encoding and is not evidence of leakage.
        assert stored_display_name.startswith("aesgcm:")

        consent = client.post(
            "/v1/matching/consent",
            headers=headers,
            json={"version": "matching-v1"},
        )
        assert consent.status_code == 204

        readiness = client.get("/v1/matching/readiness")
        assert readiness.status_code == 200
        assert readiness.json()["consent_version"] == "matching-v1"

        join = client.put(
            "/v1/matching/pool-membership",
            headers=headers,
            json={"active": True},
        )
        assert join.status_code == 409
        assert join.json()["code"] == "MATCHING_NOT_READY"

        withdraw = client.delete("/v1/matching/consent", headers=headers)
        assert withdraw.status_code == 204
        assert client.get("/v1/matching/readiness").json()["consent_version"] is None

        assert (
            client.post(
                "/v1/matching/consent",
                headers=headers,
                json={"version": "matching-v1"},
            ).status_code
            == 204
        )
        with sqlite3.connect(tmp_path / "matching.db") as database:
            consent_count, revoked_count = database.execute(
                "SELECT COUNT(*), SUM(CASE WHEN revoked_at IS NOT NULL THEN 1 ELSE 0 END) "
                "FROM matching_consents"
            ).fetchone()
        assert consent_count == 2
        assert revoked_count == 1


def test_matching_mutations_require_csrf_even_with_owner_cookie(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        csrf = _guest_with_birth(client)
        assert (
            client.post(
                "/v1/identity/claim",
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
            ).status_code
            == 200
        )

        rejected = client.put(
            "/v1/matching/profile",
            json={
                "display_name": "An",
                "gender_identity": "nonbinary",
                "intent": "open",
                "gender_preference": "everyone",
                "min_age": 24,
                "max_age": 36,
                "region_code": "ho-chi-minh",
                "weekly_intent": "de_la_can",
            },
        )
        assert rejected.status_code == 401


def test_matching_profile_rejects_region_outside_current_vietnam_catalog(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        csrf = _guest_with_birth(client)
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert client.post("/v1/identity/claim", headers=headers).status_code == 200

        rejected = client.put(
            "/v1/matching/profile",
            headers=headers,
            json={
                "display_name": "An",
                "gender_identity": "nonbinary",
                "intent": "open",
                "gender_preference": "everyone",
                "min_age": 24,
                "max_age": 36,
                "region_code": "old-province-or-injected-value",
                "weekly_intent": "de_la_can",
            },
        )

        assert rejected.status_code == 422
        assert rejected.json()["code"] == "MATCHING_PROFILE_INVALID"
