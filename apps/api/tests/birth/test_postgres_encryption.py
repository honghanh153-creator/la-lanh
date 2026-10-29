import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _correct(client: TestClient, headers: dict[str, str], birth_date: str) -> Any:
    """US-23: the explicit, fenced birth-date correction (POST refuses a different date)."""

    revision = client.get("/v1/birth-profile").json()["profile_revision"]
    return client.put(
        "/v1/birth-profile/date",
        headers=headers,
        json={
            "birth_date": birth_date,
            "confirm_birth_date": birth_date,
            "expected_revision": revision,
        },
    )


@pytest.mark.parametrize("initially_full", [False, True])
@pytest.mark.parametrize("other_birth_date", ["1990-11-15", "1990-03-16"])
def test_correcting_back_to_a_previous_birth_date_switches_current_profile_and_daily_reading(
    tmp_path: Path, initially_full: bool, other_birth_date: str
) -> None:
    database_path = tmp_path / "birth-replay.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "birth-replay-regression-123456",
            },
        )
        headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
        first = client.post("/v1/birth-profile", headers=headers, json={"birth_date": "1990-03-15"})
        assert first.status_code == 200
        first_basic_id = first.json()["snapshot_id"]
        supplement = {
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        }
        if initially_full:
            assert (
                client.post(
                    "/v1/birth-profile/supplement", headers=headers, json=supplement
                ).status_code
                == 200
            )
        # Each intermediate request must read its own current chart, not just the final one.
        for index, birth_date in enumerate(("1990-03-15", other_birth_date, "1990-03-15")):
            posted = client.post(
                "/v1/birth-profile", headers=headers, json={"birth_date": birth_date}
            )
            if index == 0:
                submitted = posted  # the same date replays the current subject
            else:
                # US-23 D4: POST never replaces an active subject; the edit does.
                assert posted.status_code == 409
                assert posted.json()["code"] == "BIRTH_DATE_CHANGE_REQUIRES_EDIT"
                submitted = _correct(client, headers, birth_date)
            assert submitted.status_code == 200
            current = client.get("/v1/birth-profile")
            assert current.status_code == 200
            assert submitted.json()["snapshot_id"] == current.json()["snapshot_id"]
            assert current.json()["birth_date"] == birth_date
            note = client.get("/v1/daily-note")
            assert note.status_code == 200
            projection = note.json()["reading_projection"]
            assert projection is not None
            with sqlite3.connect(database_path) as connection:
                note_source_id = connection.execute(
                    "SELECT chart_snapshot_id FROM daily_notes WHERE id = ?",
                    (UUID(note.json()["id"]).hex,),
                ).fetchone()[0]
                source_id = connection.execute(
                    "SELECT p.chart_snapshot_id FROM reading_revisions r "
                    "JOIN reading_plans p ON p.id = r.plan_id WHERE r.id = ?",
                    (UUID(projection["active"]["revision_id"]).hex,),
                ).fetchone()[0]
            assert UUID(note_source_id) == UUID(current.json()["snapshot_id"])
            assert UUID(source_id) == UUID(current.json()["snapshot_id"])
        # A correction replaces the subject (D1): the first snapshot is gone, not reactivated.
        corrected_id = current.json()["snapshot_id"]
        assert corrected_id != first_basic_id
        with sqlite3.connect(database_path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM chart_snapshots").fetchone()[0] == 1
        assert note.json()["persona_label"] == "Mộng"
        state = client.get("/v1/birth-profile/supplement").json()
        assert state["profile_level"] == 1
        assert state["birth_time_mode"] == "unknown"
        assert state["place_display_name"] is None
        # The supplement must now be calculated against A, not the last chart B.
        full = client.post("/v1/birth-profile/supplement", headers=headers, json=supplement)
        assert full.status_code == 200
        assert client.get("/v1/birth-profile").json()["birth_date"] == "1990-03-15"
        erased = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            headers=headers,
            json={"remove_time": True, "remove_place": True},
        )
        assert erased.status_code == 200
        assert client.get("/v1/birth-profile").json()["snapshot_id"] == corrected_id


def test_retrying_same_birth_date_preserves_full_chart_and_profile_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'same-date-retry.db'}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "same-date-retry-123456",
            },
        )
        headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
        assert (
            client.post(
                "/v1/birth-profile", headers=headers, json={"birth_date": "1990-03-15"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/v1/birth-profile/supplement",
                headers=headers,
                json={
                    "birth_time_mode": "exact",
                    "birth_time_local": "08:15",
                    "place_id": "vn-hanoi",
                    "consent_version": "birth-profile-deep-v1",
                },
            ).status_code
            == 200
        )
        before = client.get("/v1/birth-profile").json()
        before_state = client.get("/v1/birth-profile/supplement").json()

        def unexpected_compute(*args: object) -> None:
            raise AssertionError("A retry must reuse the already calculated chart")

        monkeypatch.setattr(
            app.state.birth_chart_service._engine, "calculate_date_only_sun", unexpected_compute
        )
        retried = client.post(
            "/v1/birth-profile", headers=headers, json={"birth_date": "1990-03-15"}
        )
        assert retried.status_code == 200
        assert retried.json()["snapshot_id"] == before["snapshot_id"]
        assert client.get("/v1/birth-profile").json() == before
        assert client.get("/v1/birth-profile/supplement").json() == before_state


def test_birth_replay_and_reading_reset_cannot_change_another_guest(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'two-guests.db'}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        sessions = []
        for index, birth_date in enumerate(("1990-03-15", "1990-11-15")):
            client.cookies.clear()
            guest = client.post(
                "/v1/guest-sessions",
                json={
                    "consent_version": "birth-profile-v1",
                    "purpose": "birth_profile_basic",
                    "idempotency_key": f"isolated-replay-guest-{index}-123456",
                },
            )
            headers = {
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            }
            assert (
                client.post(
                    "/v1/birth-profile", headers=headers, json={"birth_date": birth_date}
                ).status_code
                == 200
            )
            profile = client.get("/v1/birth-profile").json()
            note = client.get("/v1/daily-note").json()
            assert note["reading_projection"] is not None
            sessions.append((dict(client.cookies), headers, profile, note))

        first_cookies, first_headers, first_profile, _ = sessions[0]
        client.cookies.clear()
        client.cookies.update(first_cookies)
        for birth_date in ("1990-11-15", "1990-03-15"):
            assert _correct(client, first_headers, birth_date).status_code == 200
            assert client.get("/v1/daily-note").status_code == 200
        corrected = client.get("/v1/birth-profile").json()
        assert corrected["birth_date"] == first_profile["birth_date"]
        assert corrected["snapshot_id"] != first_profile["snapshot_id"]

        second_cookies, _, second_profile, second_note = sessions[1]
        client.cookies.clear()
        client.cookies.update(second_cookies)
        assert client.get("/v1/birth-profile").json() == second_profile
        after = client.get("/v1/daily-note").json()
        assert after["id"] == second_note["id"]
        assert after["persona_label"] == second_note["persona_label"]
        assert after["reading_projection"]["active"] == second_note["reading_projection"]["active"]
        assert after["reading_projection"]["available_update"] is None


def test_chart_snapshot_payload_is_encrypted_at_rest(tmp_path: Path) -> None:
    database_path = tmp_path / "encrypted-chart.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "encrypted-chart-guest-123456",
            },
        )
        created = client.post(
            "/v1/birth-profile",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "X-CSRF-Token": guest.json()["csrf_token"],
            },
            json={"birth_date": "1990-01-01"},
        )
        assert created.status_code == 200
        assert client.get("/v1/birth-profile").status_code == 200

    with sqlite3.connect(database_path) as connection:
        result_payload, result_ciphertext = connection.execute(
            "SELECT result_payload, result_ciphertext FROM chart_snapshots"
        ).fetchone()
    # SQL JSON adapters may encode an explicit JSON null as the literal "null".
    assert result_payload in {None, "null"}
    assert result_ciphertext.startswith("aesgcm:")
    assert "capricorn" not in result_ciphertext


@pytest.mark.parametrize("mode,place_id", [("unknown", None), ("exact", None), ("legacy", None)])
def test_precision_downgrade_cannot_keep_full_chart_before_or_after_erasure(
    tmp_path: Path, mode: str, place_id: str | None
) -> None:
    database_path = tmp_path / "precision.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "precision-downgrade-123456",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile", headers=headers, json={"birth_date": "1990-01-01"}
            ).status_code
            == 200
        )
        payload = {
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        }
        full = client.post("/v1/birth-profile/supplement", headers=headers, json=payload)
        assert full.status_code == 200
        full_snapshot_id = full.json()["snapshot_id"]
        if mode == "legacy":
            with sqlite3.connect(database_path) as connection:
                connection.execute("UPDATE birth_profiles SET profile_level = 1")
            erased = client.request(
                "DELETE",
                "/v1/birth-profile/supplement",
                headers=headers,
                json={"remove_time": True, "remove_place": True},
            )
            assert erased.status_code == 200
            assert client.get("/v1/birth-profile").json()["calculation"]["chart_type"] == (
                "date_only_natal"
            )
            with sqlite3.connect(database_path) as connection:
                assert connection.execute("SELECT COUNT(*) FROM chart_snapshots").fetchone()[0] == 1
            return
        downgraded = client.post(
            "/v1/birth-profile/supplement",
            headers=headers,
            json={
                **payload,
                "birth_time_mode": mode,
                "birth_time_local": None if mode == "unknown" else "08:15",
                "place_id": place_id,
            },
        )
        assert downgraded.status_code == 200
        current = client.get("/v1/birth-profile")
        assert current.status_code == 200
        assert current.json()["calculation"]["chart_type"] == "date_only_natal"
        assert current.json()["snapshot_id"] != full_snapshot_id
        erased = client.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            headers=headers,
            json={"remove_time": True, "remove_place": True},
        )
        assert erased.status_code == 200
        assert client.get("/v1/birth-profile").json()["calculation"]["chart_type"] == (
            "date_only_natal"
        )
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM chart_snapshots").fetchone()[0] == 1


@pytest.mark.parametrize("initially_full", [False, True])
@pytest.mark.parametrize("withdrawal_stage", ["before_save", "after_source_read"])
def test_inflight_supplement_cannot_restore_erased_precision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    initially_full: bool,
    withdrawal_stage: str,
) -> None:
    database_path = tmp_path / "stale-supplement.db"
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{database_path}",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "stale-supplement-123456",
            },
        )
        headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": guest.json()["csrf_token"]}
        assert (
            client.post(
                "/v1/birth-profile", headers=headers, json={"birth_date": "1990-01-01"}
            ).status_code
            == 200
        )
        payload = {
            "birth_time_mode": "exact",
            "birth_time_local": "08:15",
            "place_id": "vn-hanoi",
            "consent_version": "birth-profile-deep-v1",
        }
        if initially_full:
            assert (
                client.post(
                    "/v1/birth-profile/supplement", headers=headers, json=payload
                ).status_code
                == 200
            )
        repository = app.state.birth_chart_service._repository
        save = repository.save_supplement

        async def withdraw_before_save(guest_id, *args, **kwargs):  # type: ignore[no-untyped-def]
            await repository.clear_supplement(guest_id, remove_time=True, remove_place=True)
            return await save(guest_id, *args, **kwargs)

        find_current = repository.find_current

        async def withdraw_after_source_read(guest_id):  # type: ignore[no-untyped-def]
            source = await find_current(guest_id)
            await repository.clear_supplement(guest_id, remove_time=True, remove_place=True)
            return source

        if withdrawal_stage == "before_save":
            monkeypatch.setattr(repository, "save_supplement", withdraw_before_save)
        else:
            monkeypatch.setattr(repository, "find_current", withdraw_after_source_read)
        stale = client.post("/v1/birth-profile/supplement", headers=headers, json=payload)
        assert stale.status_code == 409
        assert stale.json()["code"] == "BIRTH_PROFILE_CHANGED"
        monkeypatch.setattr(repository, "find_current", find_current)
        assert client.get("/v1/birth-profile").json()["calculation"]["chart_type"] == (
            "date_only_natal"
        )
        monkeypatch.setattr(repository, "save_supplement", save)
        assert (
            client.post("/v1/birth-profile/supplement", headers=headers, json=payload).status_code
            == 200
        )
