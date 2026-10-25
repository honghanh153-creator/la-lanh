"""P02 (audit 2026-10-22): deferred matching must not collect new data.

The matching router stays mounted for existing data, but with
``matching_accepting_new_activity`` off (the default) the API creates no profile, consent or pool
membership, whatever the auth flag, birth readiness or owner claim. Withdrawal and leaving the
pool keep working for any data collected before.
"""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "http://127.0.0.1:5173"
PROFILE = {
    "display_name": "Synthetic",
    "gender_identity": "nonbinary",
    "intent": "dating",
    "gender_preference": "everyone",
    "min_age": 18,
    "max_age": 40,
    "region_code": "ho-chi-minh",
}


def _client(path: Path, *, accepting: bool | None = None) -> TestClient:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{path}",
        cors_origins=[ORIGIN],
        guest_cookie_secure=False,
        auth_enabled=False,
    )
    if accepting is not None:
        settings = settings.model_copy(update={"matching_accepting_new_activity": accepting})
    return TestClient(create_app(settings), base_url=ORIGIN)


def _owner(client: TestClient, key: str, *, birth: bool) -> dict[str, str]:
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": key,
        },
    )
    assert guest.status_code == 200
    headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
    if birth:
        assert (
            client.post("/v1/birth-profile", headers=headers, json={"birth_date": "1994-04-21"})
        ).status_code == 200
    assert client.post("/v1/identity/claim", headers=headers).status_code == 200
    return headers


def _counts(path: Path) -> tuple[int, int]:
    with sqlite3.connect(path) as db:
        profiles = db.execute("SELECT count(*) FROM matching_profiles").fetchone()[0]
        consents = db.execute("SELECT count(*) FROM matching_consents").fetchone()[0]
    return int(profiles), int(consents)


def test_default_settings_keep_matching_collection_off() -> None:
    assert Settings(environment="test").matching_accepting_new_activity is False


def test_deferred_matching_creates_no_profile_consent_or_membership(tmp_path: Path) -> None:
    path = tmp_path / "matching-off.db"
    with _client(path) as client:
        for birth in (False, True):  # the audit repro had no DOB; readiness must not matter
            headers = _owner(client, f"synthetic-matching-off-{birth}-12345678", birth=birth)
            assert (
                client.put("/v1/matching/profile", headers=headers, json=PROFILE).status_code == 410
            )
            assert (
                client.post(
                    "/v1/matching/consent", headers=headers, json={"version": "matching-v1"}
                ).status_code
                == 410
            )
            joined = client.put(
                "/v1/matching/pool-membership", headers=headers, json={"active": True}
            )
            assert joined.status_code == 410
            assert joined.headers["cache-control"].startswith("no-store")
            # Withdrawal paths stay open for data collected before the deferral.
            assert client.delete("/v1/matching/consent", headers=headers).status_code == 204
            left = client.put(
                "/v1/matching/pool-membership", headers=headers, json={"active": False}
            )
            assert left.status_code != 410
    assert _counts(path) == (0, 0)


def test_retired_collection_still_checks_origin_and_csrf_first(tmp_path: Path) -> None:
    """The gate answers 410 only to a real owner request; it is not an unauthenticated probe."""

    path = tmp_path / "matching-auth.db"
    with _client(path) as client:
        headers = _owner(client, "synthetic-matching-auth-12345678", birth=True)
        bad = {"Origin": ORIGIN, "X-CSRF-Token": "not-the-token"}
        assert client.put("/v1/matching/profile", headers=bad, json=PROFILE).status_code in {
            401,
            403,
        }
        assert client.put("/v1/matching/profile", headers=headers, json=PROFILE).status_code == 410
    assert _counts(path) == (0, 0)


def test_explicitly_reopened_matching_collects_as_before(tmp_path: Path) -> None:
    path = tmp_path / "matching-on.db"
    with _client(path, accepting=True) as client:
        headers = _owner(client, "synthetic-matching-on-12345678", birth=True)
        assert client.put("/v1/matching/profile", headers=headers, json=PROFILE).status_code == 200
        assert (
            client.post(
                "/v1/matching/consent", headers=headers, json={"version": "matching-v1"}
            ).status_code
            == 204
        )
    assert _counts(path) == (1, 1)
