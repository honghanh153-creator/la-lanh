import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_real_local_persistence_runs_guest_to_birth_reveal() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "real-local-flow-1234567890",
            },
        )
        assert guest.status_code == 200
        csrf_token = guest.json()["csrf_token"]

        birth = client.post(
            "/v1/birth-profile",
            json={"birth_date": "1990-01-01"},
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": csrf_token,
            },
        )
        assert birth.status_code == 200
        assert birth.json()["calculation"]["sign"] == "capricorn"
        assert birth.json()["calculation"]["provenance"]["engine"] == "swiss_ephemeris"

        resumed = client.get("/v1/birth-profile")
        assert resumed.status_code == 200
        assert resumed.json()["snapshot_id"] == birth.json()["snapshot_id"]


def test_real_local_persistence_runs_us03_to_us06_product_loop(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database_path = tmp_path / "u6-lifecycle.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "real-loop-1234567890abcdef",
            },
        )
        assert guest.status_code == 200
        csrf_token = guest.json()["csrf_token"]
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": csrf_token,
        }

        birth = client.post(
            "/v1/birth-profile",
            json={"birth_date": "1990-01-01"},
            headers=headers,
        )
        assert birth.status_code == 200

        daily = client.get("/v1/daily-note")
        assert daily.status_code == 200
        note_id = daily.json()["id"]
        assert daily.json()["title"]
        revision_a = daily.json()["reading_projection"]["active"]["revision_id"]

        mood = client.put(
            f"/v1/daily-note/{note_id}/mood",
            json={"mood": "Chill"},
            headers=headers,
        )
        assert mood.status_code == 200
        assert mood.json()["mood"] == "Chill"

        saved = client.put(f"/v1/daily-note/{note_id}/saved", headers=headers)
        assert saved.status_code == 200
        assert saved.json()["revision_id"] == revision_a
        assert saved.json()["reading_snapshot"]["revision_id"] == revision_a
        saved_again = client.put(f"/v1/daily-note/{note_id}/saved", headers=headers)
        assert saved_again.status_code == 200
        assert saved_again.json()["id"] == saved.json()["id"]

        share = client.post(
            f"/v1/daily-note/{note_id}/share-artifacts",
            json={"format": "story_9_16"},
            headers=headers,
        )
        assert share.status_code == 200
        assert share.json()["revision_id"] == revision_a
        assert (
            share.json()["safe_snapshot"]["title"]
            == daily.json()["reading_projection"]["active"]["sections"]["hook"]
        )
        assert "1990" not in str(share.json())

        places = client.post("/v1/birth-places/search", json={"query": "Ha"})
        assert places.status_code == 200
        assert places.json()[0]["place_id"] == "vn-hanoi"

        supplement = client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "exact",
                "birth_time_local": "08:15",
                "place_id": "vn-hanoi",
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        )
        assert supplement.status_code == 200
        assert supplement.json()["profile_level"] == 3
        assert supplement.json()["chart"]["chart_type"] == "natal"

        current_full_profile = client.get("/v1/birth-profile")
        assert current_full_profile.status_code == 200
        assert current_full_profile.json()["calculation_kind"] == "natal_chart"
        assert current_full_profile.json()["calculation"]["chart_type"] == "natal"

        daily_with_aura_available = client.get("/v1/daily-note")
        assert daily_with_aura_available.status_code == 200
        available = daily_with_aura_available.json()["reading_projection"]["available_update"]
        assert available is not None
        revision_b = available["revision_id"]
        activated = client.put(
            f"/v1/reading-projections/{daily_with_aura_available.json()['reading_projection']['scope_key']}/activate",
            json={"expected_revision_id": revision_b},
            headers=headers,
        )
        assert activated.status_code == 200
        assert activated.json()["active"]["revision_id"] == revision_b

        frozen_saved = client.get("/v1/saved-notes")
        assert frozen_saved.status_code == 200
        assert frozen_saved.json()[0]["revision_id"] == revision_a
        assert frozen_saved.json()[0]["reading_snapshot"]["revision_id"] == revision_a

        supplement_state = client.get("/v1/birth-profile/supplement")
        assert supplement_state.status_code == 200
        assert supplement_state.json()["profile_level"] == 3
        assert supplement_state.json()["place_display_name"] == "Hà Nội, Việt Nam"

        public = client.get(share.json()["public_path"].replace("/share/", "/v1/share-artifacts/"))
        assert public.status_code == 200
        assert public.json()["safe_snapshot"] == share.json()["safe_snapshot"]
        assert "evidence" not in str(public.json()).lower()
        assert "id" not in public.json()
        assert "daily_note_id" not in public.json()
        assert "public_path" not in public.json()

        removed_time = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            json={"remove_time": True, "remove_place": False},
            headers=headers,
        )
        assert removed_time.status_code == 200
        assert removed_time.json()["profile_level"] == 1
        assert removed_time.json()["birth_time_mode"] == "unknown"
        assert removed_time.json()["place_display_name"] == "Hà Nội, Việt Nam"

        with sqlite3.connect(database_path) as raw:
            purge_counts = {
                table: int(raw.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
                for table in (
                    "daily_notes",
                    "saved_notes",
                    "share_artifacts",
                    "reading_plans",
                    "reading_revisions",
                    "reading_projections",
                    "reading_generation_attempts",
                )
            }
            remaining_chart_types = raw.execute("SELECT COUNT(*) FROM chart_snapshots").fetchone()[
                0
            ]
        assert purge_counts == {table: 0 for table in purge_counts}
        assert remaining_chart_types == 1
        assert (
            client.get(
                share.json()["public_path"].replace("/share/", "/v1/share-artifacts/")
            ).status_code
            == 404
        )

        after_precision_removal = client.get("/v1/daily-note")
        assert after_precision_removal.status_code == 200
        active_after_removal = after_precision_removal.json()["reading_projection"]["active"]
        assert active_after_removal["mode"] == "vibe_fallback"
        assert active_after_removal["revision_id"] != revision_b

        removed_place = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            json={"remove_time": False, "remove_place": True},
            headers=headers,
        )
        assert removed_place.status_code == 200
        assert removed_place.json()["place_display_name"] is None

        claimed = client.post("/v1/identity/claim", headers=headers)
        assert claimed.status_code == 200
        assert client.cookies.get("la_lanh_owner") is not None

        with sqlite3.connect(database_path) as raw:
            stale_owner = raw.execute(
                "SELECT guest_id, profile_id, id FROM reading_plans LIMIT 1"
            ).fetchone()
        assert stale_owner is not None

        deleted = client.delete("/v1/guest-session", headers=headers)
        assert deleted.status_code == 204
        assert client.cookies.get("la_lanh_guest") is None
        assert client.cookies.get("la_lanh_csrf") is None
        assert client.cookies.get("la_lanh_owner") is None
        assert client.get("/v1/session").status_code == 401
        deleted_share = client.get(
            share.json()["public_path"].replace("/share/", "/v1/share-artifacts/")
        )
        assert deleted_share.status_code == 404

        with sqlite3.connect(database_path) as raw:
            raw.execute("PRAGMA foreign_keys=ON")
            counts = {
                table: int(
                    raw.execute(
                        f"SELECT COUNT(*) FROM {table}"  # noqa: S608 - closed tuple below.
                    ).fetchone()[0]
                )
                for table in (
                    "reading_plans",
                    "reading_revisions",
                    "reading_projections",
                    "saved_notes",
                    "share_artifacts",
                    "principals",
                    "owner_sessions",
                    "la_chung_requests",
                )
            }
            assert counts == {table: 0 for table in counts}
            guest_id, profile_id, stale_plan_id = stale_owner
            with pytest.raises(sqlite3.IntegrityError):
                raw.execute(
                    """
                    INSERT INTO reading_revisions (
                        id, guest_id, profile_id, plan_id, revision_key, source,
                        renderer_version, content_version, schema_version, rules_version,
                        gate_policy_version, accepted, evaluation_ciphertext, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid4().hex,
                        guest_id,
                        profile_id,
                        stale_plan_id,
                        "f" * 64,
                        "deterministic",
                        "late-worker",
                        "late-worker",
                        "reading-candidate/v1",
                        "factor-planner-v1",
                        "evidence:v1+anti_influence:v1+editorial:v1+privacy:v1",
                        True,
                        "late-worker-ciphertext",
                        "2026-09-07 12:00:00.000000",
                    ),
                )
