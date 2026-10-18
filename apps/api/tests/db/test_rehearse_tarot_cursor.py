"""The cursor rehearsal's portable part runs on SQLite here; the PostgreSQL role/RLS part runs only
in infra/hetzner/rehearse-migration.sh against the disposable restored database."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.session import Database
from scripts import rehearse_tarot_cursor


async def test_cursor_rehearsal_passes_and_leaves_nothing_behind(tmp_path: Path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'rehearsal.db'}"
    db = Database(url)
    await db.initialize()
    await db.dispose()
    await rehearse_tarot_cursor.rehearse(url)
    db = Database(url)
    try:
        from sqlalchemy import func, select

        from app.domains.guest.tables import GuestSessionRow
        from app.domains.tarot.tables import TarotSessionRow, TarotVariantCursorRow

        async with db.sessions() as session:
            for table in (GuestSessionRow, TarotSessionRow, TarotVariantCursorRow):
                assert await session.scalar(select(func.count()).select_from(table)) == 0
    finally:
        await db.dispose()


async def test_cursor_rehearsal_fails_when_a_deletion_rewinds_the_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative control: a service whose delete also drops the cursor must fail the rehearsal."""

    from sqlalchemy import delete

    from app.domains.tarot.service import TarotSessionService
    from app.domains.tarot.tables import TarotVariantCursorRow

    url = f"sqlite+aiosqlite:///{tmp_path / 'rehearsal.db'}"
    db = Database(url)
    await db.initialize()
    await db.dispose()
    original = TarotSessionService.delete

    async def rewinding_delete(self: TarotSessionService, guest_id, session_id) -> None:  # type: ignore[no-untyped-def]
        await original(self, guest_id, session_id)
        async with self._sessions() as session, session.begin():
            await session.execute(
                delete(TarotVariantCursorRow).where(TarotVariantCursorRow.guest_id == guest_id)
            )

    monkeypatch.setattr(TarotSessionService, "delete", rewinding_delete)
    with pytest.raises(rehearse_tarot_cursor.RehearsalFailed, match="deletion-rewound"):
        await rehearse_tarot_cursor.rehearse(url)


def test_main_reports_a_code_without_details(monkeypatch: pytest.MonkeyPatch, capsys) -> None:  # type: ignore[no-untyped-def]
    async def failing(_: str) -> None:
        raise rehearse_tarot_cursor.RehearsalFailed("connection-role-is-superuser")

    monkeypatch.setenv("LA_LANH_DATABASE_URL", "postgresql+asyncpg://secret@host/db")
    monkeypatch.setattr(rehearse_tarot_cursor, "rehearse", failing)
    assert rehearse_tarot_cursor.main() == 1
    out = capsys.readouterr().out
    assert out.strip() == "tarot-cursor-rehearsal-failed:connection-role-is-superuser"
    assert "secret" not in out


def test_rehearsal_script_runs_the_app_as_the_least_privileged_backend_role() -> None:
    """Static contract of infra/hetzner/rehearse-migration.sh (it needs Docker and a backup, so it
    runs on the server): the app never connects as the container superuser."""

    script = (
        Path(__file__).resolve().parents[4] / "infra/hetzner/rehearse-migration.sh"
    ).read_text()
    assert 'BACKEND_ROLE="la_lanh_rehearsal_backend"' in script
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS" in script
    assert '--role="$BACKEND_ROLE"' in script  # restored objects owned by the backend role
    assert "tableowner <> '${BACKEND_ROLE}'" in script
    url_line = next(line for line in script.splitlines() if "postgresql+asyncpg://" in line)
    assert "postgres:" not in url_line and "%s:%s@" in url_line
    assert '"$BACKEND_ROLE" "$backend_password"' in script
    order = [
        script.index("run_app alembic upgrade head"),
        script.index("run_app python -m scripts.check_database_privacy"),
        script.index("run_app python -m scripts.rehearse_tarot_cursor"),
        script.index("Rehearsal readiness OK"),
    ]
    assert order == sorted(order)
    assert "PASSWORD :'pw'" in script  # the password is not on a command line
