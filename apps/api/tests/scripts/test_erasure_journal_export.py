"""P07 option A: hourly host copy of the deletion journal and the dump exclusion (text checks).

No systemd or Docker in CI: whether the timer fires and files appear on the VPS is operator
evidence.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
INFRA = REPO_ROOT / "infra/hetzner"
SYSTEMD = INFRA / "systemd"


def _unit(name: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in (SYSTEMD / name).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith(("#", "[")):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), []).append(value.strip())
    return values


def test_journal_copy_runs_hourly_sandboxed_and_alerts_on_failure() -> None:
    timer = _unit("la-lanh-erasure-journal.timer")
    assert timer["OnCalendar"] == ["*-*-* *:05:00 UTC"]
    assert timer["Persistent"] == ["true"]
    assert timer["Unit"] == ["la-lanh-erasure-journal.service"]
    service = _unit("la-lanh-erasure-journal.service")
    assert service["ExecStart"] == ["/opt/la-lanh/current/infra/hetzner/export-erasure-journal.sh"]
    assert service["OnFailure"] == ["la-lanh-alert@%n.service"]
    assert service["ReadWritePaths"] == ["/opt/la-lanh/backups"]
    assert service["UMask"] == ["0077"]
    assert service["ProtectSystem"] == ["strict"]


def test_export_writes_private_files_then_applies_journal_retention() -> None:
    script = (INFRA / "export-erasure-journal.sh").read_text()
    assert "set -euo pipefail" in script
    assert 'install -d -m 0700 "$JOURNAL_DIR"' in script and "umask 077" in script
    assert 'run export > "${out}.partial"' in script and 'chmod 0600 "$out"' in script
    assert script.index("run export") < script.index("run purge")  # copy before trimming
    assert "database_url" not in script  # credentials stay inside the app container


def test_installer_and_dump_cover_the_journal() -> None:
    installer = (INFRA / "install-backup-timer.sh").read_text()
    for unit in ("la-lanh-erasure-journal.service", "la-lanh-erasure-journal.timer"):
        assert unit in installer
    assert "systemctl is-active --quiet la-lanh-erasure-journal.timer" in installer
    dump = (INFRA / "backup-database.sh").read_text()
    assert "--schema=public --exclude-table-data=public.erasure_journal" in dump
