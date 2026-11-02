"""US-23: correcting a saved birth date (PUT /v1/birth-profile/date). Real app on SQLite with
foreign keys on, synthetic data. PostgreSQL evidence for AC2/AC4/AC8/AC11 is the gated probe in
tests/birth/test_postgres_date_correction_probe.py.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import Database
from app.domains.birth.errors import BirthChartBusy
from app.domains.content_rewrite.tables import RewriteSendFenceRow
from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.replay import export_entries, replay
from app.domains.erasure_journal.tables import ErasureJournalRow
from tests.saved.copy_flow import (
    BIRTH_DATE,
    ORIGIN,
    count,
    hex_id,
    make_app,
    raw,
    save_and_share,
    start_guest,
)

NEW_DATE = "1992-07-20"
SUPPLEMENT = {
    "birth_time_mode": "exact",
    "birth_time_local": "08:15",
    "place_id": "vn-hanoi",
    "consent_version": "birth-profile-deep-v1",
}
DERIVED = (
    "daily_notes",
    "reading_plans",
    "reading_revisions",
    "reading_projections",
    "reading_generation_attempts",
    "mood_check_ins",
)


def _correct(
    client: TestClient,
    headers: dict[str, str],
    birth_date: str = NEW_DATE,
    *,
    confirm: str | None = None,
    revision: str | None = None,
) -> Any:
    if revision is None:
        revision = client.get("/v1/birth-profile").json()["profile_revision"]
    return client.put(
        "/v1/birth-profile/date",
        headers=headers,
        json={
            "birth_date": birth_date,
            "confirm_birth_date": confirm or birth_date,
            "expected_revision": revision,
        },
    )


def _full_subject(client: TestClient, headers: dict[str, str]) -> Any:
    assert client.post("/v1/birth-profile/supplement", json=SUPPLEMENT, headers=headers).status_code
    copies = save_and_share(client, headers)
    note = client.get("/v1/daily-note").json()
    assert client.put(
        f"/v1/daily-note/{note['id']}/mood", json={"mood": "Chill"}, headers=headers
    ).status_code
    return copies


def _state(database_path: Path) -> dict[str, Any]:
    with raw(database_path) as connection:
        profile = connection.execute(
            "SELECT current_snapshot_id, updated_at, profile_level, birth_time_ciphertext, "
            "birth_place_ciphertext, supplement_consent_version FROM birth_profiles"
        ).fetchone()
        return {
            "profile": profile,
            "snapshots": connection.execute("SELECT COUNT(*) FROM chart_snapshots").fetchone()[0],
            **{
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
                for table in (*DERIVED, "saved_notes", "share_artifacts", "birth_date_changes")
            },
        }


def test_a_correction_replaces_the_full_subject_and_keeps_saved_and_shared_copies(
    tmp_path: Path,
) -> None:
    """AC2, AC12 and Codex r54 #1: an active natal subject is corrected without an FK error."""

    database_path = tmp_path / "correct.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        copies = _full_subject(client, headers)
        before = client.get("/v1/birth-profile").json()
        assert before["calculation_kind"] == "natal_chart" and before["profile_revision"]
        assert _state(database_path)["snapshots"] == 2

        corrected = _correct(client, headers)
        assert corrected.status_code == 200, corrected.text
        assert corrected.headers["cache-control"].startswith("no-store")
        body = corrected.json()
        assert body["birth_date"] == NEW_DATE and body["calculation_kind"] == "date_only_sun"
        assert body["resumed"] is False and body["profile_revision"] != before["profile_revision"]
        assert client.get("/v1/birth-profile").json()["snapshot_id"] == body["snapshot_id"]

        state = _state(database_path)
        assert state["snapshots"] == 1
        assert {table: state[table] for table in DERIVED} == dict.fromkeys(DERIVED, 0)
        level, time_value, place, consent = state["profile"][2:]
        assert (level, time_value, place, consent) == (1, None, None, None)
        assert (state["saved_notes"], state["share_artifacts"], state["birth_date_changes"]) == (
            1,
            1,
            1,
        )
        supplement = client.get("/v1/birth-profile/supplement").json()
        assert (
            supplement["birth_time_mode"] == "unknown" and supplement["place_display_name"] is None
        )

        # Today's note is rebuilt from the new date; the frozen copies stay manageable.
        rebuilt = client.get("/v1/daily-note")
        assert rebuilt.status_code == 200 and rebuilt.json()["id"] != copies.note_id
        assert [item["daily_note_id"] for item in client.get("/v1/saved-notes").json()] == [
            copies.note_id
        ]
        # The owner link list arrives in U3; here the kept link is checked by its public path.
        assert client.get(copies.public_path).status_code == 200
        assert client.delete(f"/v1/share-artifacts/{copies.share_id}", headers=headers).status_code
        assert client.get(copies.public_path).status_code == 404
        assert client.delete(f"/v1/daily-note/{copies.note_id}/saved", headers=headers).status_code
        assert client.get("/v1/saved-notes").json() == []

        with raw(database_path) as connection:
            journal = connection.execute(
                "SELECT kind, scope, length(subject_digest) FROM erasure_journal "
                "WHERE kind = 'birth_date_replaced'"
            ).fetchall()
        assert journal == [(ErasureKind.BIRTH_DATE_REPLACED.value, "", 32)]


def test_the_same_date_is_reported_and_changes_nothing(tmp_path: Path) -> None:
    """AC3."""

    database_path = tmp_path / "same.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        before = _state(database_path)
        same = _correct(client, headers, BIRTH_DATE)
        assert same.status_code == 409 and same.json()["code"] == "BIRTH_DATE_UNCHANGED"
        assert _state(database_path) == before


def test_a_stale_revision_from_another_tab_is_refused(tmp_path: Path) -> None:
    """AC4: the second tab's fence is stale; nothing changes, it must reload."""

    database_path = tmp_path / "race.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        revision = client.get("/v1/birth-profile").json()["profile_revision"]
        assert _correct(client, headers, NEW_DATE, revision=revision).status_code == 200
        after_first = _state(database_path)
        stale = _correct(client, headers, "1993-01-02", revision=revision)
        assert stale.status_code == 409 and stale.json()["code"] == "BIRTH_PROFILE_CHANGED"
        assert stale.headers["cache-control"].startswith("no-store")
        assert _state(database_path) == after_first
        assert client.get("/v1/birth-profile").json()["birth_date"] == NEW_DATE


def test_a_fourth_change_in_24_hours_is_refused_and_the_window_rolls(tmp_path: Path) -> None:
    """AC5 (D5)."""

    database_path = tmp_path / "limit.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        for birth_date in ("1991-01-01", "1992-02-02", "1993-03-03"):
            assert _correct(client, headers, birth_date).status_code == 200
        before = _state(database_path)
        limited = _correct(client, headers, "1994-04-04")
        assert limited.status_code == 429 and limited.json()["code"] == "BIRTH_DATE_CHANGE_LIMITED"
        assert _state(database_path) == before
        assert client.get("/v1/birth-profile").json()["birth_date"] == "1993-03-03"

        old = (datetime.now(UTC) - timedelta(hours=25)).isoformat(sep=" ")
        with raw(database_path) as connection:
            connection.execute("UPDATE birth_date_changes SET changed_at = ?", (old,))
        assert _correct(client, headers, "1994-04-04").status_code == 200
        assert count(database_path, "birth_date_changes") == 1  # expired rows pruned


def test_a_compute_failure_keeps_the_old_chart_and_its_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC6: phase 1 writes nothing."""

    database_path = tmp_path / "compute.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        _full_subject(client, headers)
        before = _state(database_path)

        async def busy(*_args: Any) -> Any:
            raise BirthChartBusy

        monkeypatch.setattr(app.state.birth_chart_service, "_run_compute", busy)
        refused = _correct(client, headers)
        assert refused.status_code == 429 and refused.json()["code"] == "BIRTH_CHART_BUSY"
        assert _state(database_path) == before


def test_a_failure_inside_the_replacement_transaction_rolls_everything_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC6, phase 2: a failed journal write undoes the deletes, the counter and the switch."""

    database_path = tmp_path / "rollback.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN, raise_server_exceptions=True) as client:
        headers = start_guest(client)
        _full_subject(client, headers)
        before = _state(database_path)
        journal = app.state.erasure_journal

        def failing_record(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("journal unavailable")

        monkeypatch.setattr(journal, "record", failing_record)
        with pytest.raises(RuntimeError, match="journal unavailable"):
            _correct(client, headers)
        assert _state(database_path) == before


def test_post_never_replaces_an_active_subject(tmp_path: Path) -> None:
    """AC7 (D4)."""

    database_path = tmp_path / "post.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        before = _state(database_path)
        posted = client.post("/v1/birth-profile", json={"birth_date": NEW_DATE}, headers=headers)
        assert posted.status_code == 409
        assert posted.json()["code"] == "BIRTH_DATE_CHANGE_REQUIRES_EDIT"
        assert _state(database_path) == before
        same = client.post("/v1/birth-profile", json={"birth_date": BIRTH_DATE}, headers=headers)
        assert same.status_code == 200 and same.json()["resumed"] is True


@pytest.mark.parametrize("years", [17, 121])
def test_an_out_of_range_date_is_refused_before_compute_and_never_logged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    years: int,
) -> None:
    """AC9 and AC10 (D6): refused before any read or compute; nothing changes or is kept."""

    database_path = tmp_path / "age.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        save_and_share(client, headers)
        before = _state(database_path)
        computed: list[object] = []

        async def spy(*args: Any) -> Any:
            computed.append(args)
            raise AssertionError("a refused date must not be computed")

        monkeypatch.setattr(app.state.birth_chart_service, "_run_compute", spy)
        refused_date = date.today().replace(year=date.today().year - years).isoformat()
        with caplog.at_level(logging.DEBUG):
            refused = _correct(client, headers, refused_date)
        assert refused.status_code == 422 and refused.json()["code"] == "BIRTH_DATE_OUT_OF_RANGE"
        assert refused_date not in refused.text
        assert computed == []
        assert _state(database_path) == before
        assert refused_date not in caplog.text and BIRTH_DATE not in caplog.text
        assert "BIRTH_DATE_OUT_OF_RANGE" in caplog.text


def test_input_checks_session_and_logs(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Confirmation typo check, CSRF/origin, no subject, and data-free logs (AC10)."""

    database_path = tmp_path / "checks.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client, caplog.at_level(logging.DEBUG):
        headers = start_guest(client)
        mismatch = _correct(client, headers, NEW_DATE, confirm="1992-07-21")
        assert mismatch.status_code == 422
        assert mismatch.json()["code"] == "BIRTH_DATE_CONFIRMATION_MISMATCH"
        revision = client.get("/v1/birth-profile").json()["profile_revision"]
        payload = {"birth_date": NEW_DATE, "confirm_birth_date": NEW_DATE}
        no_csrf = client.put(
            "/v1/birth-profile/date",
            headers={"Origin": ORIGIN},
            json={**payload, "expected_revision": revision},
        )
        assert no_csrf.status_code in {401, 403}
        foreign = client.put(
            "/v1/birth-profile/date",
            headers={**headers, "Origin": "https://evil.example"},
            json={**payload, "expected_revision": revision},
        )
        assert foreign.status_code == 403
        extra = client.put(
            "/v1/birth-profile/date",
            headers=headers,
            json={**payload, "expected_revision": revision, "birth_time_local": "08:00"},
        )
        assert extra.status_code == 422
        assert client.get("/v1/birth-profile").json()["birth_date"] == BIRTH_DATE
        assert _correct(client, headers).status_code == 200
        client.cookies.clear()
        fresh = start_guest(client)
        with raw(database_path) as connection:
            connection.execute(
                "UPDATE birth_profiles SET current_snapshot_id = NULL WHERE guest_id = ("
                "SELECT guest_id FROM birth_profiles ORDER BY created_at DESC LIMIT 1)"
            )
        missing = _correct(client, fresh, revision=datetime.now(UTC).isoformat())
        assert missing.status_code == 404
    for value in (NEW_DATE, BIRTH_DATE, "1992-07-21"):
        assert value not in caplog.text


def test_restore_replay_fails_closed_before_and_keeps_the_subject_after(tmp_path: Path) -> None:
    """AC8 and Codex r54 #1: both dump sides; the pre-correction side leaves no subject."""

    database_path = tmp_path / "live.db"
    before_dump, after_dump = tmp_path / "before.db", tmp_path / "after.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        copies = _full_subject(client, headers)
        shutil.copyfile(database_path, before_dump)
        corrected = _correct(client, headers)
        assert corrected.status_code == 200
        shutil.copyfile(database_path, after_dump)
        journal, envelope = app.state.erasure_journal, app.state.birth_chart_service._envelope
        lines = client.portal.call(export_entries, app.state.database.sessions)  # type: ignore[union-attr]
        cookies = dict(client.cookies)
    assert all(NEW_DATE not in line and BIRTH_DATE not in line for line in lines)

    def _replay(path: Path) -> Any:
        restored = Database(f"sqlite+aiosqlite:///{path}")

        async def run() -> Any:
            try:
                return await replay(restored.sessions, journal, envelope, lines)
            finally:
                await restored.dispose()

        return asyncio.run(run())

    kind = ErasureKind.BIRTH_DATE_REPLACED.value
    after = _replay(after_dump)
    assert after.reflected[kind] == 1 and not after.applied[kind]
    with raw(after_dump) as connection:
        current = connection.execute("SELECT current_snapshot_id FROM birth_profiles").fetchone()
    assert current[0] == hex_id(corrected.json()["snapshot_id"])

    before = _replay(before_dump)
    assert before.applied[kind] == 1
    state = _state(before_dump)
    assert state["profile"][0] is None and state["snapshots"] == 0
    assert {table: state[table] for table in DERIVED} == dict.fromkeys(DERIVED, 0)
    assert state["profile"][2:] == (1, None, None, None)
    assert (state["saved_notes"], state["share_artifacts"]) == (1, 1)
    with raw(before_dump) as connection:
        status = connection.execute("SELECT onboarding_status FROM guest_sessions").fetchone()[0]
    assert status == "birth_pending"
    assert _replay(before_dump).reflected[kind] == 1  # idempotent

    # The restored person is asked for the date again, and POST accepts it: no subject exists.
    restored_app = make_app(before_dump)
    with TestClient(restored_app, base_url=ORIGIN) as client:
        client.cookies.update(cookies)
        assert client.get("/v1/birth-profile").status_code == 404
        reentered = client.post("/v1/birth-profile", json={"birth_date": NEW_DATE}, headers=headers)
        assert reentered.status_code == 200 and reentered.json()["birth_date"] == NEW_DATE
        assert [item["daily_note_id"] for item in client.get("/v1/saved-notes").json()] == [
            copies.note_id
        ]


def test_success_waits_for_a_send_admitted_before_the_correction(tmp_path: Path) -> None:
    """AC11: the captured provider send drains after commit and before success."""

    database_path = tmp_path / "drain.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        start_guest(client)
        before = client.get("/v1/birth-profile").json()
        sessions = app.state.database.sessions
        guest_hex = raw(database_path).execute("SELECT id FROM guest_sessions").fetchone()[0]
        guest_id = UUID(guest_hex)
        job_id, lease = uuid4(), uuid4()

        async def admit() -> None:
            async with sessions() as session, session.begin():
                session.add(
                    RewriteSendFenceRow(
                        job_id=job_id,
                        lease_token=lease,
                        subject_id=guest_id,
                        expires_at=datetime.now(UTC) + timedelta(minutes=3),
                    )
                )

        assert client.portal is not None
        client.portal.call(admit)
        service = app.state.birth_chart_service
        future = client.portal.start_task_soon(
            lambda: service.correct_date(
                guest_id=guest_id,
                birth_date=date.fromisoformat(NEW_DATE),
                confirm_birth_date=date.fromisoformat(NEW_DATE),
                expected_revision=datetime.fromisoformat(before["profile_revision"]),
            )
        )
        # Poll read-only: an HTTP read also renews the guest row, and a tight loop of those
        # writes could starve the correction's writer transaction on SQLite under load.
        deadline = datetime.now(UTC) + timedelta(seconds=10)
        while True:
            connection = raw(database_path)
            try:
                (changes,) = connection.execute(
                    "SELECT count(*) FROM birth_date_changes"
                ).fetchall()
            finally:
                connection.close()  # no lingering shared lock in front of the writer
            if changes[0] == 1:
                break
            assert datetime.now(UTC) < deadline, "the replacement did not commit"
            time.sleep(0.02)
        assert client.get("/v1/birth-profile").json()["birth_date"] == NEW_DATE
        assert not future.done(), "success must wait for the admitted send"

        async def finish_send() -> None:
            async with sessions() as session, session.begin():
                row = await session.scalar(
                    select(RewriteSendFenceRow).where(RewriteSendFenceRow.job_id == job_id)
                )
                assert row is not None
                await session.delete(row)

        client.portal.call(finish_send)
        reveal = future.result(timeout=5)
        assert reveal.birth_date.isoformat() == NEW_DATE


def test_the_correction_endpoint_shares_the_birth_compute_bucket() -> None:
    from app.middleware.admission import _policy

    class _Request:
        method = "PUT"
        url = type("Url", (), {"path": "/v1/birth-profile/date"})()

    policy = _policy(_Request())  # type: ignore[arg-type]
    assert policy is not None and policy.name == "birth-compute"


async def test_journal_rows_hold_no_birth_value(tmp_path: Path) -> None:
    """The entry is the kind, a 32-byte keyed digest, an empty scope and a time."""

    assert {column.name for column in ErasureJournalRow.__table__.columns} == {
        "id",
        "kind",
        "subject_digest",
        "scope",
        "occurred_at",
    }


def test_cleanup_prunes_change_counters_after_their_window(tmp_path: Path) -> None:
    from app.domains.guest.postgres import PostgresGuestRepository

    database_path = tmp_path / "prune.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        assert _correct(client, headers).status_code == 200
        guests = PostgresGuestRepository(app.state.database.sessions)
        assert client.portal is not None
        client.portal.call(guests.purge_expired, datetime.now(UTC), 100)
        assert count(database_path, "birth_date_changes") == 1  # inside the window: kept
        client.portal.call(guests.purge_expired, datetime.now(UTC) + timedelta(hours=25), 100)
        assert count(database_path, "birth_date_changes") == 0


def test_the_counter_migration_is_private_and_reversible() -> None:
    from importlib import import_module
    from unittest.mock import MagicMock, patch

    migration: Any = import_module("migrations.versions.20261029_0040_birth_date_changes")
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    with (
        patch.object(migration.op, "get_bind", return_value=bind),
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "create_index"),
        patch.object(migration.op, "execute") as execute,
    ):
        migration.upgrade()
    assert table.call_args.args[0] == "birth_date_changes"
    columns = {column.name for column in table.call_args.args[1:]}
    assert columns == {"id", "guest_id", "changed_at"}  # no date, no value
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    assert "ENABLE ROW LEVEL SECURITY" in sql and "REVOKE ALL" in sql
    with (
        patch.object(migration.op, "drop_index"),
        patch.object(migration.op, "drop_table") as drop,
    ):
        migration.downgrade()
    drop.assert_called_once_with("birth_date_changes")
