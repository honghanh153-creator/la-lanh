"""Production wiring and schema for the deletion journal (audit P07, option A)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.main import create_app

ROOT = Path(__file__).resolve().parents[4]
MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations/versions/20261023_0038_erasure_journal.py"
)


def test_every_explicit_erasure_path_gets_the_same_journal(tmp_path: Path) -> None:
    app = create_app(
        Settings(environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path / 'w.db'}")
    )
    with TestClient(app):
        journal = app.state.erasure_journal
        state = app.state
        wired = {
            "guest": state.guest_session_service._repository._erasure_journal,
            "history": state.history_service._repository._erasure_journal,
            "birth": state.birth_chart_service._repository._erasure_journal,
            "matching": state.matching_service._repository._erasure_journal,
            "radar": state.radar_service._erasure_journal,
            "resonance": state.resonance_service._repository._erasure_journal,
        }
        assert {name: value is journal for name, value in wired.items()} == dict.fromkeys(
            wired, True
        )


def test_migration_creates_a_private_table_matching_the_model() -> None:
    source = MIGRATION.read_text()
    assert 'down_revision: str | Sequence[str] | None = "20261018_0037"' in source
    assert "ENABLE ROW LEVEL SECURITY" in source
    assert "REVOKE ALL ON TABLE public.erasure_journal FROM PUBLIC" in source
    assert "'anon', 'authenticated'" in source
    for column in ErasureJournalRow.__table__.columns:
        assert f'"{column.name}"' in source, column.name
    # Pseudonymous facts only: no content-bearing column.
    assert {c.name for c in ErasureJournalRow.__table__.columns} == {
        "id", "kind", "subject_digest", "scope", "occurred_at",
    }  # fmt: skip


def test_backups_carry_the_table_but_not_its_entries() -> None:
    backup = (ROOT / "infra/hetzner/backup-database.sh").read_text()
    assert "--exclude-table-data=public.erasure_journal" in backup


def test_cli_exports_imports_and_replays_without_ids(tmp_path: Path) -> None:
    import json
    import os
    import subprocess
    import sys

    env = {
        **os.environ,
        "LA_LANH_ENVIRONMENT": "test",
        "LA_LANH_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'cli.db'}",
    }
    api = Path(__file__).resolve().parents[2]

    def cli(*args: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed module, synthetic arguments
            [sys.executable, "-m", "scripts.erasure_journal", *args],
            cwd=api, env=env, check=True, capture_output=True, text=True,
        ).stdout  # fmt: skip

    assert cli("export") == ""
    entry = {
        "kind": "history_cleared",
        "subject_digest": "cd" * 32,
        "scope": "",
        "occurred_at": "2026-10-23T12:00:00+00:00",
    }
    exported = tmp_path / "journal.jsonl"
    exported.write_text(json.dumps(entry) + "\n")
    assert "Imported 1" in cli("import", str(exported))
    assert [json.loads(line) for line in cli("export").splitlines()] == [entry]
    replayed = cli("replay", "--since", "2026-10-23T00:00:00+00:00")
    assert "history_cleared: entries=1 applied=0 unmatched=1" in replayed
    assert "cleanup" in replayed


def test_six_hourly_expired_cleanup_also_applies_journal_retention() -> None:
    source = (Path(__file__).resolve().parents[2] / "scripts/cleanup_expired.py").read_text()
    assert "purge_entries(" in source
    assert "settings.erasure_journal_retention_days" in source
