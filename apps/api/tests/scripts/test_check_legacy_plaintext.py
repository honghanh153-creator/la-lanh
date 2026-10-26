"""P06 (audit 2026-10-22): the legacy-plaintext check counts rows and never prints a value."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import update

from app.db.session import Database
from app.domains.daily.tables import DailyNoteRow
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from scripts import check_legacy_plaintext
from scripts.check_legacy_plaintext import CHECKS, count_legacy
from tests.experiments.test_postgres import NOW, _create_target
from tests.history.test_daily_window_dependencies import _cipher


async def _database(path: Path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{path}")
    await database.initialize()
    envelope = _cipher()
    target = await _create_target(database, envelope)
    share = await PostgresShareArtifactRepository(database.sessions, envelope).create(
        ShareArtifactRecord(
            id=target.daily_note_id,
            guest_id=target.guest_id,
            daily_note_id=target.daily_note_id,
            token_hash=b"t" * 32,
            safe_snapshot=SafeShareSnapshot(*(["zqsecretcanary"] * 8)),
            format=ShareFormat.SQUARE_1_1,
            created_at=NOW,
            expires_at=NOW.replace(year=NOW.year + 1),
        )
    )
    return database, target, share


async def _counts(database: Database) -> dict[str, int]:
    async with database.engine.connect() as connection:
        return await count_legacy(connection)


@pytest.mark.asyncio
async def test_current_writes_count_zero_and_legacy_rows_are_counted(tmp_path: Path) -> None:
    database, target, share = await _database(tmp_path / "legacy.db")
    try:
        assert await _counts(database) == dict.fromkeys((c.key for c in CHECKS), 0)
        async with database.sessions() as session, session.begin():
            await session.execute(
                update(DailyNoteRow)
                .where(DailyNoteRow.id == target.daily_note_id)
                .values(content_ciphertext=None, title="zqsecretcanary")
            )
            await session.execute(
                update(ShareArtifactRow)
                .where(ShareArtifactRow.id == share.id)
                .values(safe_snapshot={"title": "zqsecretcanary"})
            )
        counts = await _counts(database)
        assert counts["daily_notes.unencrypted"] == 1
        assert counts["daily_notes.plaintext_beside_ciphertext"] == 0
        assert counts["share_artifacts.plaintext_beside_ciphertext"] == 1
        assert sum(counts.values()) == 2
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_main_prints_counts_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "print.db"
    database, target, _ = await _database(path)
    async with database.sessions() as session, session.begin():
        await session.execute(
            update(DailyNoteRow)
            .where(DailyNoteRow.id == target.daily_note_id)
            .values(content_ciphertext=None, title="zqsecretcanary")
        )
    await database.dispose()
    monkeypatch.setenv("LA_LANH_DATABASE_URL", f"sqlite+aiosqlite:///{path}")
    assert await _run_main([]) == 0
    assert await _run_main(["--fail-on-legacy"]) == 1
    out = capsys.readouterr().out
    assert "legacy_plaintext_counts" in out
    for secret in ("zqsecretcanary", str(target.guest_id), str(target.daily_note_id), str(path)):
        assert secret not in out


async def _run_main(argv: list[str]) -> int:
    import asyncio

    return await asyncio.to_thread(check_legacy_plaintext.main, argv)


def test_failure_message_names_only_the_error_type(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(
        "LA_LANH_DATABASE_URL", "postgresql+asyncpg://user:zqpassword@127.0.0.1:1/db"
    )
    assert check_legacy_plaintext.main([]) == 1
    out = capsys.readouterr().out
    assert out.startswith("legacy-plaintext-check-failed:") and "zqpassword" not in out
