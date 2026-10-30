"""US-24 U5 wiring: migration, settings, the minute timer (as text) and the operator commands."""

from __future__ import annotations

import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings

API_ROOT = Path(__file__).resolve().parents[2]
INFRA = API_ROOT.parents[1] / "infra/hetzner"


def test_bridge_tables_are_private() -> None:
    migration = import_module("migrations.versions.20261030_0042_human_tarot_sheet_bridge")
    assert migration.down_revision == "20261030_0041"
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    with (
        patch.object(migration.op, "create_table") as table,
        patch.object(migration.op, "execute") as execute,
        patch.object(migration.op, "get_bind", return_value=bind),
    ):
        migration.upgrade()
    assert {call.args[0] for call in table.call_args_list} == set(migration.TABLES)
    sql = "\n".join(call.args[0] for call in execute.call_args_list)
    for name in migration.TABLES:
        assert f"ALTER TABLE public.{name} ENABLE ROW LEVEL SECURITY" in sql


def test_sync_needs_the_sheet_and_launch_approval() -> None:
    with pytest.raises(ValueError, match="Sheet id"):
        Settings(environment="test", human_tarot_sheet_sync_enabled=True)
    configured = Settings(
        environment="test",
        human_tarot_sheet_sync_enabled=True,
        human_tarot_sheet_id="synthetic-sheet-id-0000000000",
        human_tarot_google_credentials_file="/run/secrets/synthetic.json",
    )
    assert configured.human_tarot_sheet() == (
        "synthetic-sheet-id-0000000000",
        "/run/secrets/synthetic.json",
    )
    with pytest.raises(ValueError, match="not configured"):
        Settings(environment="test").human_tarot_sheet()
    with pytest.raises(ValueError):
        Settings(environment="test", human_tarot_sheet_id="https://docs.google.com/x")


def _unit(name: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in (INFRA / "systemd" / name).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith(("#", "[")):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), []).append(value.strip())
    return values


def test_the_minute_timer_runs_one_pass_inside_the_app_container() -> None:
    timer = _unit("la-lanh-human-tarot-sync.timer")
    assert timer["OnCalendar"] == ["*-*-* *:*:15"]
    assert timer["Unit"] == ["la-lanh-human-tarot-sync.service"]
    service = _unit("la-lanh-human-tarot-sync.service")
    assert service["ExecStart"] == ["/usr/local/sbin/la-lanh-human-tarot-sync"]
    assert service["OnFailure"] == ["la-lanh-alert@%n.service"]
    assert service["TimeoutStartSec"] == ["50s"]
    runner = (INFRA / "run-human-tarot-sync.sh").read_text(encoding="utf-8")
    assert 'exec docker exec "${container}" python -m scripts.sync_human_tarot' in runner
    # Never installed by the existing installers: the owner turns it on separately.
    for installer in ("install-retention-timers.sh", "install-backup-timer.sh", "deploy.sh"):
        assert "human-tarot" not in (INFRA / installer).read_text(encoding="utf-8")


def _script(*args: str, tmp_path: Any, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed interpreter and module, no user input
        [sys.executable, "-m", *args],
        cwd=API_ROOT,
        env={
            **{key: value for key, value in os.environ.items() if not key.startswith("LA_LANH_")},
            "LA_LANH_ENVIRONMENT": "test",
            "LA_LANH_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'ops.db'}",
            **env,
        },
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_operator_commands(tmp_path: Any) -> None:
    disabled = _script("scripts.sync_human_tarot", tmp_path=tmp_path)
    assert disabled.returncode == 0 and disabled.stdout.strip() == "human_tarot_sync disabled"
    closed = _script("scripts.sync_human_tarot", "close-today", tmp_path=tmp_path)
    assert closed.returncode == 0 and closed.stdout.startswith("human_tarot_intake_closed day=")
    replayed = _script("scripts.erasure_journal", "replay", "/dev/null", tmp_path=tmp_path)
    assert replayed.returncode == 0, replayed.stderr[-400:]
    assert "human_tarot_intake_closed day=" in replayed.stdout


def test_the_owner_template_carries_the_exact_header_and_the_catalog() -> None:
    import zipfile
    from xml.etree import ElementTree

    from app.domains.human_tarot import sheet_rows

    template = API_ROOT.parents[1] / "docs/operations/human-tarot-sheet-template.xlsx"
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    strings: set[str] = set()
    with zipfile.ZipFile(template) as archive:
        sheets = archive.read("xl/workbook.xml").decode()
        for name in archive.namelist():
            if name.startswith("xl/worksheets/") or name == "xl/sharedStrings.xml":
                root = ElementTree.fromstring(archive.read(name))  # noqa: S314 - repo file
                strings |= {node.text or "" for node in root.iter(f"{namespace}t")}
    assert set(sheet_rows.HEADER) <= strings
    assert set(sheet_rows.catalog_titles()) <= strings
    assert f'name="{sheet_rows.TAB}"' in sheets
