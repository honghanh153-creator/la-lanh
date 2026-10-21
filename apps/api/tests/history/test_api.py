import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event, select

from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.tables import ContentRewriteJobRow, RewriteSendFenceRow
from app.domains.guest.tables import GuestSessionRow
from tests.accounts.support import FakeTransport, guest, headers
from tests.accounts.support import client as make_client
from tests.content_rewrite.test_repository import _record
from tests.history.test_retention import cipher


def disclosed_guest(client: TestClient) -> dict[str, object]:
    created = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "synthetic-history-disclosed-123456",
            "history_consent_version": "history-retention-v1",
        },
    )
    assert created.status_code == 200
    return cast(dict[str, object], created.json())


def test_new_guest_policy_and_acknowledged_history_only_clear(tmp_path: Path) -> None:
    fake = FakeTransport()
    with make_client(tmp_path / "history.db", fake, enabled=False) as client:
        owner = disclosed_guest(client)
        status = client.get("/v1/session/history-retention")
        assert status.status_code == 200
        assert status.json() == {
            "enabled": True,
            "history_days": 30,
            "daily_note_hours": 24,
            "activated_at": status.json()["activated_at"],
            "saved_notes_kept": True,
        }
        assert status.json()["activated_at"] is not None
        activated = client.post(
            "/v1/session/history-retention",
            headers=headers(owner["csrf_token"]),
            json={"consent_version": "history-retention-v1"},
        )
        assert activated.json() == status.json()
        assert client.delete("/v1/session/history").status_code == 403
        assert client.delete("/v1/session/history", headers=headers("wrong")).status_code == 403
        cleared = client.delete("/v1/session/history", headers=headers(owner["csrf_token"]))
        assert cleared.status_code == 204
        assert all("Max-Age=0" not in value for value in cleared.headers.get_list("Set-Cookie"))
        assert client.get("/v1/session").json()["session_epoch"] == owner["session_epoch"]
        assert fake.calls == []


def test_old_client_guest_stays_disabled_until_explicit_opt_in(tmp_path: Path) -> None:
    with make_client(tmp_path / "old-client.db", FakeTransport(), enabled=False) as client:
        owner = guest(client)
        disabled = client.get("/v1/session/history-retention")
        assert disabled.json() == {
            "enabled": False,
            "history_days": 30,
            "daily_note_hours": 24,
            "activated_at": None,
            "saved_notes_kept": True,
        }
        consent = {"consent_version": "history-retention-v1"}
        activated = client.post(
            "/v1/session/history-retention", headers=headers(owner["csrf_token"]), json=consent
        )
        assert activated.status_code == 200 and activated.json()["enabled"] is True
        replay = client.post(
            "/v1/session/history-retention", headers=headers(owner["csrf_token"]), json=consent
        )
        assert replay.json() == activated.json()


def test_creation_history_consent_is_bound_to_idempotency_and_atomic(tmp_path: Path) -> None:
    with make_client(tmp_path / "atomic.db", FakeTransport(), enabled=False) as client:
        owner = guest(client)
        conflict = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "synthetic-guest-idempotency-123456",
                "history_consent_version": "history-retention-v1",
            },
        )
        assert conflict.status_code == 409
        assert client.get("/v1/session/history-retention").json()["enabled"] is False
        assert client.get("/v1/session").json()["session_epoch"] == owner["session_epoch"]
        disclosed_guest(client)
        before = client.get("/v1/session/history-retention").json()
        disclosed_guest(client)
        assert client.get("/v1/session/history-retention").json() == before
        rejected = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "synthetic-history-invalid-123456",
                "history_consent_version": "unknown",
            },
        )
        assert rejected.status_code == 422
        with sqlite3.connect(tmp_path / "atomic.db") as connection:
            assert connection.execute("SELECT count(*) FROM guest_sessions").fetchone() == (2,)
            assert connection.execute(
                "SELECT count(*) FROM history_retention_policies"
            ).fetchone() == (1,)
            assert connection.execute(
                "SELECT count(*) FROM history_retention_policies p JOIN guest_sessions g "
                "ON p.guest_id = g.id WHERE p.activated_at = g.created_at "
                "AND p.consent_version = 'history-retention-v1'"
            ).fetchone() == (1,)


def test_new_account_consent_activates_history_without_changing_owner(tmp_path: Path) -> None:
    from tests.accounts.support import sign_in

    fake = FakeTransport()
    with make_client(tmp_path / "account.db", fake) as client:
        owner = guest(client)
        assert client.get("/v1/session/history-retention").json()["enabled"] is False
        signed_in = sign_in(client, owner["csrf_token"])
        assert client.get("/v1/session/history-retention").json()["enabled"] is True
        cleared = client.delete(
            "/v1/session/history", headers=headers(signed_in.json()["session"]["csrf_token"])
        )
        assert cleared.status_code == 204
        assert client.get("/v1/account").json()["signed_in"] is True
        with sqlite3.connect(tmp_path / "account.db") as connection:
            assert connection.execute("SELECT count(*) FROM guest_sessions").fetchone() == (1,)
            assert connection.execute("SELECT count(*) FROM accounts").fetchone() == (1,)
            assert connection.execute("SELECT count(*) FROM account_devices").fetchone() == (1,)


def test_missing_credentials_and_invalid_consent_cannot_mutate(tmp_path: Path) -> None:
    with make_client(tmp_path / "rejected.db", FakeTransport(), enabled=False) as client:
        assert client.get("/v1/session/history-retention").status_code == 401
        assert client.delete("/v1/session/history", headers=headers("x")).status_code == 401
        owner = guest(client)
        before = client.get("/v1/session/history-retention").json()
        rejected = client.post(
            "/v1/session/history-retention",
            headers=headers(owner["csrf_token"]),
            json={"consent_version": "unknown"},
        )
        assert rejected.status_code == 422
        assert client.get("/v1/session/history-retention").json() == before


def test_busy_api_returns_retry_without_acknowledgement_or_cookie_erasure(tmp_path: Path) -> None:
    with make_client(tmp_path / "busy.db", FakeTransport(), enabled=False) as client:
        owner = guest(client)
        database = cast(FastAPI, client.app).state.database

        async def seed_marker() -> None:
            async with database.sessions() as session, session.begin():
                guest_id = await session.scalar(select(GuestSessionRow.id))
                row = PostgresContentRewriteRepository(database.sessions, cipher())._row(_record())
                row.owner_guest_id = guest_id
                row.status, row.lease_token = "leased", uuid4()
                row.request_started_at = datetime.now(UTC)
                row.lease_expires_at = row.request_started_at + timedelta(minutes=1)
                session.add(row)
                assert guest_id is not None and row.lease_token is not None
                session.add(
                    RewriteSendFenceRow(
                        job_id=row.id,
                        lease_token=row.lease_token,
                        subject_id=guest_id,
                        expires_at=row.request_started_at + timedelta(minutes=2),
                    )
                )

        assert client.portal is not None
        client.portal.call(seed_marker)
        response = client.delete("/v1/session/history", headers=headers(owner["csrf_token"]))
        assert response.status_code == 409 and response.json()["code"] == "HISTORY_BUSY"
        assert response.headers["Retry-After"] == "1"
        assert client.get("/v1/session").json()["session_epoch"] == owner["session_epoch"]

        async def marker_kept() -> bool:
            async with database.sessions() as session:
                row = await session.scalar(select(ContentRewriteJobRow))
                return row is not None and row.request_started_at is not None

        assert client.portal.call(marker_kept)


def test_creation_policy_failure_rolls_back_guest_and_consent(tmp_path: Path) -> None:
    path = tmp_path / "rollback.db"
    with make_client(path, FakeTransport(), enabled=False) as client:
        database = cast(FastAPI, client.app).state.database

        def reject_policy(*args: object) -> None:
            statement = str(args[2])
            if statement.startswith("INSERT INTO history_retention_policies"):
                raise RuntimeError("synthetic policy write failure")

        event.listen(database.engine.sync_engine, "before_cursor_execute", reject_policy)
        try:
            with pytest.raises(RuntimeError, match="synthetic policy write failure"):
                disclosed_guest(client)
        finally:
            event.remove(database.engine.sync_engine, "before_cursor_execute", reject_policy)
        with sqlite3.connect(path) as connection:
            for table in (
                "guest_sessions",
                "consents",
                "guest_session_creations",
                "history_retention_policies",
            ):
                assert connection.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)  # noqa: S608


def test_expired_credentials_cannot_clear_or_activate_or_create_guest(tmp_path: Path) -> None:
    path = tmp_path / "expired.db"
    with make_client(path, FakeTransport(), enabled=False) as client:
        owner = guest(client)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "UPDATE guest_sessions SET created_at = '2020-01-01 00:00:00', "
                "expires_at = '2020-02-01 00:00:00'"
            )
        assert (
            client.delete("/v1/session/history", headers=headers(owner["csrf_token"])).status_code
            == 401
        )
        assert (
            client.post(
                "/v1/session/history-retention",
                headers=headers(owner["csrf_token"]),
                json={"consent_version": "history-retention-v1"},
            ).status_code
            == 401
        )
        with sqlite3.connect(path) as connection:
            assert connection.execute("SELECT count(*) FROM guest_sessions").fetchone() == (1,)
            assert connection.execute(
                "SELECT count(*) FROM history_retention_policies"
            ).fetchone() == (0,)
