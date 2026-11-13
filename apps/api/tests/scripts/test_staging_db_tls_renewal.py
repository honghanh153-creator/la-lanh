"""Staging DB TLS renewal (incident 2026-11-10: the 30-day pair expired and staging was down ~44 h).

The renewal script runs for real with real OpenSSL certificates. `docker` is a logging stub and the
pair maker is make-db-tls.sh without its chown lines (no root in CI). Unit files are checked as
text: whether the timer fires on the VPS is operator evidence in the release receipt.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
INFRA = REPO_ROOT / "infra/hetzner"
SYSTEMD = INFRA / "systemd"
RENEW = INFRA / "staging/renew-db-tls.sh"
MAKE = INFRA / "make-db-tls.sh"


def _unit(name: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in (SYSTEMD / name).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith(("#", "[")):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), []).append(value.strip())
    return values


def test_timer_runs_daily_and_failures_raise_the_marker() -> None:
    timer = _unit("la-lanh-staging-db-tls.timer")
    assert timer["OnCalendar"] == ["*-*-* 03:40:00 UTC"]
    assert timer["Persistent"] == ["true"]
    assert timer["Unit"] == ["la-lanh-staging-db-tls.service"]
    service = _unit("la-lanh-staging-db-tls.service")
    assert service["ExecStart"] == [
        "/opt/la-lanh/staging/source/infra/hetzner/staging/renew-db-tls.sh"
    ]
    assert service["OnFailure"] == ["la-lanh-alert@%n.service"]
    assert service["ProtectSystem"] == ["strict"]
    assert service["ReadWritePaths"] == ["/opt/la-lanh/staging/secrets"]
    assert service["UMask"] == ["0077"]


def test_installer_ships_the_units_and_needs_root() -> None:
    installer = (INFRA / "staging/install-db-tls-timer.sh").read_text(encoding="utf-8")
    for name in (
        "la-lanh-staging-db-tls.service",
        "la-lanh-staging-db-tls.timer",
        "la-lanh-alert@.service",
    ):
        assert (SYSTEMD / name).exists()
        assert name in installer
    assert 'EUID}" -ne 0' in installer
    assert "/opt/la-lanh/staging/source/infra/hetzner/staging" in installer


def _maker(tmp_path: Path, days: int) -> Path:
    """make-db-tls.sh with a chosen lifetime and without chown (tests do not run as root)."""
    text = MAKE.read_text(encoding="utf-8").replace("-days 30", f"-days {days}")
    lines = [line for line in text.splitlines() if not line.startswith("chown ")]
    path = tmp_path / f"make-{days}.sh"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def fake_docker(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "docker"
    stub.write_text(
        "#!/bin/sh\n"
        'echo "$*" >> "$FAKE_DOCKER_LOG"\n'
        'if [ "$1" = inspect ]; then echo "${FAKE_HEALTH:-healthy}"; fi\n'
        'if [ "$1" = ps ]; then echo "${FAKE_WORKER_ID:-}"; fi\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return bin_dir


def _secrets(tmp_path: Path, days: int) -> Path:
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    subprocess.run([str(_maker(tmp_path, days)), str(secrets / "tls"), "db"], check=True)  # noqa: S603
    (secrets / "db_ca.pem").write_bytes((secrets / "tls/ca.pem").read_bytes())
    return secrets


def _renew(
    tmp_path: Path, secrets: Path, bin_dir: Path, **env: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["/bin/bash", str(RENEW)],
        env={
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "LA_LANH_STAGING_SECRETS_DIR": str(secrets),
            "LA_LANH_MAKE_DB_TLS": str(_maker(tmp_path, 30)),
            "LA_LANH_STAGING_HEALTH_TIMEOUT_SECONDS": "5",
            "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
            **env,
        },
        capture_output=True,
        text=True,
        check=False,
    )


def _docker_calls(tmp_path: Path) -> list[str]:
    log = tmp_path / "docker.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _valid_beyond(cert: Path, days: int) -> bool:
    command = ["openssl", "x509", "-checkend", str(days * 86400), "-noout", "-in", str(cert)]
    result = subprocess.run(command, capture_output=True, check=False)  # noqa: S603
    return result.returncode == 0


def test_a_fresh_pair_is_left_alone(tmp_path: Path, fake_docker: Path) -> None:
    secrets = _secrets(tmp_path, 30)
    before = (secrets / "tls/server.crt").read_bytes()
    result = _renew(tmp_path, secrets, fake_docker)
    assert result.returncode == 0, result.stderr
    assert "Staging DB TLS OK" in result.stdout
    assert (secrets / "tls/server.crt").read_bytes() == before
    assert _docker_calls(tmp_path) == []
    assert not list(secrets.glob("tls.prev-*"))


def test_an_expiring_pair_is_renewed_and_staging_restarted(
    tmp_path: Path, fake_docker: Path
) -> None:
    secrets = _secrets(tmp_path, 5)
    old_cert = (secrets / "tls/server.crt").read_bytes()
    (secrets / "tls.prev-20200101T000000Z").mkdir()  # an older archive is pruned
    result = _renew(tmp_path, secrets, fake_docker)
    assert result.returncode == 0, result.stderr
    assert "renewed" in result.stdout
    assert _valid_beyond(secrets / "tls/server.crt", 25)
    assert (secrets / "db_ca.pem").read_bytes() == (secrets / "tls/ca.pem").read_bytes()
    archives = list(secrets.glob("tls.prev-*"))
    assert len(archives) == 1
    assert (archives[0] / "server.crt").read_bytes() == old_cert
    assert not (secrets / "tls.new").exists()
    assert not (secrets / "tls.pending-restart").exists()
    calls = _docker_calls(tmp_path)
    assert calls[0] == "restart la-lanh-staging-db-1"
    assert "restart la-lanh-staging-staging-app-1" in calls
    assert calls.index("restart la-lanh-staging-staging-app-1") > calls.index(
        "inspect --format {{.State.Health.Status}} la-lanh-staging-db-1"
    )
    # Nothing secret reaches the journal.
    assert "PRIVATE KEY" not in result.stdout + result.stderr
    assert "BEGIN CERTIFICATE" not in result.stdout + result.stderr


def test_an_app_ca_copy_that_drifted_triggers_a_renewal(tmp_path: Path, fake_docker: Path) -> None:
    secrets = _secrets(tmp_path, 30)
    (secrets / "db_ca.pem").write_text("stale\n", encoding="utf-8")
    result = _renew(tmp_path, secrets, fake_docker)
    assert result.returncode == 0, result.stderr
    assert (secrets / "db_ca.pem").read_bytes() == (secrets / "tls/ca.pem").read_bytes()


@pytest.mark.parametrize("maker", ["fails", "short-lived"])
def test_a_bad_new_pair_leaves_the_current_one_untouched(
    tmp_path: Path, fake_docker: Path, maker: str
) -> None:
    secrets = _secrets(tmp_path, 5)
    before = {f: (secrets / "tls" / f).read_bytes() for f in ("server.crt", "server.key", "ca.pem")}
    make = "/usr/bin/false" if maker == "fails" else str(_maker(tmp_path, 5))
    result = _renew(tmp_path, secrets, fake_docker, LA_LANH_MAKE_DB_TLS=make)
    assert result.returncode != 0
    assert {f: (secrets / "tls" / f).read_bytes() for f in before} == before
    assert _docker_calls(tmp_path) == []
    assert not (secrets / "tls.new").exists()


def test_an_unhealthy_database_after_restart_fails_loudly(
    tmp_path: Path, fake_docker: Path
) -> None:
    secrets = _secrets(tmp_path, 5)
    result = _renew(
        tmp_path,
        secrets,
        fake_docker,
        FAKE_HEALTH="unhealthy",
        LA_LANH_STAGING_HEALTH_TIMEOUT_SECONDS="1",
    )
    assert result.returncode == 1
    assert "la-lanh-staging-db-1 is not healthy" in result.stderr
    assert "restart la-lanh-staging-staging-app-1" not in _docker_calls(tmp_path)
    assert (secrets / "tls.pending-restart").exists()

    # The next run sees fresh files on disk but must still finish the restarts, not report success.
    (tmp_path / "docker.log").unlink()
    again = _renew(tmp_path, secrets, fake_docker)
    assert again.returncode == 0, again.stderr
    assert "did not finish its restarts" in again.stdout
    calls = _docker_calls(tmp_path)
    assert "restart la-lanh-staging-db-1" in calls
    assert "restart la-lanh-staging-staging-app-1" in calls
    assert not (secrets / "tls.pending-restart").exists()

    # Only then does a run report the pair as OK and leave the containers alone.
    (tmp_path / "docker.log").unlink()
    third = _renew(tmp_path, secrets, fake_docker)
    assert "Staging DB TLS OK" in third.stdout
    assert _docker_calls(tmp_path) == []


@pytest.mark.parametrize("running", [True, False])
def test_the_generation_worker_reloads_the_ca_only_when_it_runs(
    tmp_path: Path, fake_docker: Path, running: bool
) -> None:
    secrets = _secrets(tmp_path, 5)
    env = {"FAKE_WORKER_ID": "abc123"} if running else {}
    result = _renew(tmp_path, secrets, fake_docker, **env)
    assert result.returncode == 0, result.stderr
    calls = _docker_calls(tmp_path)
    worker = "la-lanh-staging-staging-rewrite-worker-1"
    if running:
        app = "restart la-lanh-staging-staging-app-1"
        assert calls.index(f"restart {worker}") > calls.index(app)
        assert f"inspect --format {{{{.State.Health.Status}}}} {worker}" in calls
    else:
        assert not any(worker in c and not c.startswith("ps ") for c in calls)
        assert not any(c.startswith(("start", "up", "compose")) for c in calls)
    assert not (secrets / "tls.pending-restart").exists()


def test_missing_pair_or_bad_setting_fails(tmp_path: Path, fake_docker: Path) -> None:
    secrets = _secrets(tmp_path, 30)
    (secrets / "tls/server.key").unlink()
    assert _renew(tmp_path, secrets, fake_docker).returncode == 1
    bad = _renew(tmp_path, secrets, fake_docker, LA_LANH_STAGING_TLS_RENEW_DAYS="30")
    assert bad.returncode == 2
    assert _docker_calls(tmp_path) == []
