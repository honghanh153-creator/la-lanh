"""O02/P07 (audit 2026-10-22): daily backup timer, freshness check and failure marker.

The freshness script runs for real against synthetic files. Unit files are checked as text: no
systemd is available in CI, so whether the timer actually fires on the VPS is operator evidence.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
INFRA = REPO_ROOT / "infra/hetzner"
SYSTEMD = INFRA / "systemd"
CHECK = INFRA / "check-backup-freshness.sh"


def _unit(name: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in (SYSTEMD / name).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith(("#", "[")):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), []).append(value.strip())
    return values


def test_backup_runs_daily_and_verifies_itself() -> None:
    timer = _unit("la-lanh-backup.timer")
    assert timer["OnCalendar"] == ["*-*-* 20:10:00"]
    assert timer["Persistent"] == ["true"]
    assert timer["Unit"] == ["la-lanh-backup.service"]
    service = _unit("la-lanh-backup.service")
    assert service["ExecStart"] == ["/opt/la-lanh/current/infra/hetzner/backup-database.sh"]
    assert service["ExecStartPost"] == [
        "/opt/la-lanh/current/infra/hetzner/check-backup-freshness.sh"
    ]
    assert service["OnFailure"] == ["la-lanh-alert@%n.service"]
    assert service["ProtectSystem"] == ["strict"]
    assert service["ReadWritePaths"] == ["/opt/la-lanh/backups"]
    assert service["UMask"] == ["0077"]


def test_an_independent_check_catches_a_stopped_backup_timer() -> None:
    timer = _unit("la-lanh-backup-check.timer")
    assert timer["OnCalendar"] == ["*-*-* 02,08,14,20:50:00"]
    service = _unit("la-lanh-backup-check.service")
    assert service["ExecStart"] == ["/opt/la-lanh/current/infra/hetzner/check-backup-freshness.sh"]
    assert service["OnFailure"] == ["la-lanh-alert@%n.service"]
    assert "ReadWritePaths" not in service  # read-only check


def test_failure_marker_is_an_err_journal_entry_and_a_file() -> None:
    exec_start = _unit("la-lanh-alert@.service")["ExecStart"][0]
    assert "/var/lib/la-lanh/alerts/%i.failed" in exec_start
    assert "systemd-cat -t la-lanh-alert -p err" in exec_start


def test_installer_ships_every_backup_unit() -> None:
    installer = (INFRA / "install-backup-timer.sh").read_text(encoding="utf-8")
    for name in (
        "la-lanh-backup.service",
        "la-lanh-backup.timer",
        "la-lanh-backup-check.service",
        "la-lanh-backup-check.timer",
        "la-lanh-alert@.service",
    ):
        assert (SYSTEMD / name).exists()
        assert name in installer
    assert 'EUID}" -ne 0' in installer


def _dump(directory: Path, name: str, body: bytes = b"synthetic dump") -> Path:
    path = directory / name
    path.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    (directory / f"{name}.sha256").write_text(f"{digest}  {name}\n")
    return path


def _check(directory: Path, max_age: str = "26") -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["/bin/bash", str(CHECK)],
        env={
            "PATH": os.environ["PATH"],
            "LA_LANH_BACKUP_DIR": str(directory),
            "LA_LANH_BACKUP_MAX_AGE_HOURS": max_age,
        },
        capture_output=True,
        text=True,
        check=False,
    )


def test_fresh_backup_with_matching_checksum_passes(tmp_path: Path) -> None:
    _dump(tmp_path, "la-lanh-20261022T201000Z.dump")
    result = _check(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Backup OK" in result.stdout


def test_newest_backup_decides_even_when_older_ones_are_valid(tmp_path: Path) -> None:
    old = _dump(tmp_path, "la-lanh-20261020T201000Z.dump")
    stamp = time.time() - 48 * 3600
    os.utime(old, (stamp, stamp))
    newest = _dump(tmp_path, "la-lanh-20261022T201000Z.dump")
    newest.write_bytes(b"tampered after checksum")
    assert _check(tmp_path).returncode == 1


@pytest.mark.parametrize(
    ("case", "expected"),
    [("missing-dir", 1), ("no-dump", 1), ("empty", 1), ("no-checksum", 1), ("stale", 1)],
)
def test_unhealthy_backups_fail(tmp_path: Path, case: str, expected: int) -> None:
    directory = tmp_path / "backups"
    if case != "missing-dir":
        directory.mkdir()
    if case == "empty":
        _dump(directory, "la-lanh-20261022T201000Z.dump", b"")
    if case == "no-checksum":
        (directory / "la-lanh-20261022T201000Z.dump").write_bytes(b"synthetic dump")
    if case == "stale":
        path = _dump(directory, "la-lanh-20261020T201000Z.dump")
        stamp = time.time() - 27 * 3600
        os.utime(path, (stamp, stamp))
    result = _check(directory)
    assert result.returncode == expected, (result.stdout, result.stderr)
    assert result.stderr


def test_invalid_age_setting_is_rejected(tmp_path: Path) -> None:
    _dump(tmp_path, "la-lanh-20261022T201000Z.dump")
    assert _check(tmp_path, max_age="0").returncode == 2
    assert _check(tmp_path, max_age="1d").returncode == 2
