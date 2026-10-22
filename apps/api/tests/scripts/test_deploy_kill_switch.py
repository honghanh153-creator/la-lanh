"""Behavioural regression for the deploy kill switch (PR #40 review).

Runs the real ``infra/hetzner/deploy.sh`` and ``compose-files.sh`` against a fake ``docker`` that
records every command. This proves the script's ordering and branching only; it is not evidence
of real Docker or Compose behaviour (for example that ``compose rm -sf`` with no worker exits 0),
which the fake models from the documented CLI contract.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
RELEASE = "newrelease01"
PREVIOUS = "oldrelease01"

FAKE_DOCKER = r"""#!/usr/bin/env bash
# Records each call as: <LA_LANH_RELEASE_ID>|<COMPOSE_PROFILES>|<args...>
printf '%s|%s|%s\n' "${LA_LANH_RELEASE_ID:-}" "${COMPOSE_PROFILES:-}" "$*" >> "$FAKE_LOG"
args=" $* "
case "$args" in
  *" compose version "*) exit 0 ;;
  *" image inspect "*) [[ "${FAKE_RELEASE_IMAGE:-0}" == 1 ]] && exit 0 || exit 1 ;;
  " inspect "*) printf '%s\n' "${FAKE_RUNNING_IMAGE:-}"; exit 0 ;;
esac
case "$args" in
  *" config --quiet "*) exit 0 ;;
  *" ps -q app "*) [[ -n "${FAKE_RUNNING_IMAGE:-}" ]] && echo running-app-container; exit 0 ;;
  *" rm -sf rewrite-worker "*)
    [[ "${FAKE_RM_FAIL:-0}" == 1 ]] && { echo "rm failed" >&2; exit 1; }
    [[ "${FAKE_WORKER_ABSENT:-0}" == 1 ]] && echo "No stopped containers"
    exit 0 ;;
  *" build app "*)
    [[ "${FAKE_BUILD_FAIL:-0}" == 1 ]] && { echo "build failed" >&2; exit 1; }
    touch "$FAKE_LOG.built"; exit 0 ;;
  *"Settings().generation_enabled"*)
    [[ "${FAKE_SETTINGS_FAIL:-0}" == 1 && ! -e "$FAKE_LOG.built" ]] && exit 1
    built="$FAKE_LOG.built"
    if [[ -e "$built" ]]; then echo "${FAKE_POST:-false}"; else echo "${FAKE_PRE:-false}"; fi
    exit 0 ;;
  *) exit 0 ;;
esac
"""

FAKE_STAT = r"""#!/usr/bin/env bash
# GNU-style stat for require_secret_file on any host.
case "$2" in
  %a) echo 600 ;;
  %u:%g) echo 65532:65532 ;;
  *) exit 1 ;;
esac
"""


@dataclass
class Run:
    returncode: int
    calls: list[tuple[str, str, str]]
    stdout: str
    stderr: str

    def index(self, needle: str) -> int:
        return next(i for i, (_, _, args) in enumerate(self.calls) if needle in args)

    def has(self, needle: str) -> bool:
        return any(needle in args for _, _, args in self.calls)

    def compose_calls(self) -> list[str]:
        return [args for _, _, args in self.calls if args.startswith("compose -f")]


def _deploy(tmp_path: Path, *, auth: bool = False, **fake: str) -> Run:
    return _deploy_with(tmp_path, fake, auth=auth)


def _deploy_with(tmp_path: Path, fake: dict[str, str], *, auth: bool = False) -> Run:
    infra = tmp_path / "root" / "infra" / "hetzner"
    infra.mkdir(parents=True)
    for name in ("deploy.sh", "compose-files.sh"):
        shutil.copy(REPO_ROOT / "infra/hetzner" / name, infra / name)
    for name in ("compose.yaml", "compose.auth.yaml", "run-retention-job.sh"):
        (infra / name).write_text("# synthetic\n")
    (infra / "app.env").write_text("LA_LANH_SWISSEPH_LICENSE_MODE=agpl\n")
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    names = ["database_url", "guest_hash_key", "guest_encryption_key", "openai_api_key"]
    if auth:
        names.append("supabase_admin_key")
    for name in names:
        (secrets / name).write_text("synthetic-only\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("docker", FAKE_DOCKER), ("stat", FAKE_STAT), ("curl", "#!/bin/sh\n")):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    log = tmp_path / "docker.log"
    log.write_text("")
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "APP_HOSTNAME": "synthetic.invalid",
        "LA_LANH_SECRETS_DIR": str(secrets),
        "LA_LANH_RELEASE_ID": RELEASE,
        "FAKE_LOG": str(log),
        **fake,
    }
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(infra / "deploy.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    calls: list[tuple[str, str, str]] = []
    for line in log.read_text().splitlines():
        release, profiles, args = line.split("|", 2)
        calls.append((release, profiles, args))
    return Run(result.returncode, calls, result.stdout, result.stderr)


def test_generation_off_stops_the_worker_before_a_failing_build(tmp_path: Path) -> None:
    run = _deploy(
        tmp_path, FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}", FAKE_PRE="false", FAKE_BUILD_FAIL="1"
    )
    assert run.returncode != 0
    assert run.index("rm -sf rewrite-worker") < run.index("build app")
    assert not run.has(" up -d")
    # Settings was read in the running app's image, with this release's compose files.
    settings = next(call for call in run.calls if "Settings().generation_enabled" in call[2])
    assert settings[0] == PREVIOUS


def test_release_image_is_preferred_for_the_preflight_settings(tmp_path: Path) -> None:
    run = _deploy(
        tmp_path,
        FAKE_RELEASE_IMAGE="1",
        FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}",
        FAKE_PRE="false",
        FAKE_BUILD_FAIL="1",
    )
    settings = next(call for call in run.calls if "Settings().generation_enabled" in call[2])
    assert settings[0] == RELEASE
    assert not run.has("ps -q app")
    assert run.index("rm -sf rewrite-worker") < run.index("build app")


@pytest.mark.parametrize(
    "fake",
    [
        {},  # first deploy: no release image and no running app to ask
        {"FAKE_RUNNING_IMAGE": f"la-lanh:{PREVIOUS}", "FAKE_SETTINGS_FAIL": "1"},
        {"FAKE_RUNNING_IMAGE": "unexpected:tag"},
    ],
    ids=["no-image", "settings-unreadable", "foreign-image"],
)
def test_unknown_preflight_fails_safe_by_stopping_the_worker(
    tmp_path: Path, fake: dict[str, str]
) -> None:
    run = _deploy_with(tmp_path, {"FAKE_BUILD_FAIL": "1", **fake})
    assert run.returncode != 0
    assert run.index("rm -sf rewrite-worker") < run.index("build app")
    assert "stopping any rewrite worker before build" in run.stdout


def test_generation_on_keeps_the_worker_and_starts_it_with_the_profile(tmp_path: Path) -> None:
    run = _deploy(
        tmp_path, FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}", FAKE_PRE="true", FAKE_POST="true"
    )
    assert run.returncode == 0, run.stderr
    assert not run.has("rm -sf rewrite-worker")
    ups = [profiles for _, profiles, args in run.calls if " up -d" in args]
    assert ups and all(profiles == "generation" for profiles in ups)


def test_generation_off_after_build_still_removes_the_worker(tmp_path: Path) -> None:
    """Preflight said true (older image), the release image says false: removed after build."""

    run = _deploy(
        tmp_path, FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}", FAKE_PRE="true", FAKE_POST="false"
    )
    assert run.returncode == 0, run.stderr
    assert run.index("build app") < run.index("rm -sf rewrite-worker") < run.index(" up -d")
    assert all(profiles == "" for _, profiles, args in run.calls if " up -d" in args)


def test_failing_worker_removal_blocks_the_deploy(tmp_path: Path) -> None:
    run = _deploy(
        tmp_path, FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}", FAKE_PRE="false", FAKE_RM_FAIL="1"
    )
    assert run.returncode != 0
    assert not run.has("build app")
    assert not run.has(" up -d")


def test_absent_worker_is_a_successful_no_op(tmp_path: Path) -> None:
    run = _deploy(
        tmp_path,
        FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}",
        FAKE_PRE="false",
        FAKE_POST="false",
        FAKE_WORKER_ABSENT="1",
    )
    assert run.returncode == 0, run.stderr
    assert run.has(" up -d")


@pytest.mark.parametrize("auth", [False, True])
def test_every_compose_call_uses_the_same_project_files(tmp_path: Path, auth: bool) -> None:
    run = _deploy(
        tmp_path,
        auth=auth,
        FAKE_RUNNING_IMAGE=f"la-lanh:{PREVIOUS}",
        FAKE_PRE="false",
        FAKE_POST="false",
    )
    assert run.returncode == 0, run.stderr
    infra = tmp_path / "root" / "infra" / "hetzner"
    files = f"-f {infra}/compose.yaml" + (f" -f {infra}/compose.auth.yaml" if auth else "")
    calls = run.compose_calls()
    assert calls and all(call.startswith(f"compose {files} ") for call in calls)
    if not auth:
        assert not any("compose.auth.yaml" in call for call in calls)
    removal = [call for call in calls if "rm -sf rewrite-worker" in call]
    assert len(removal) == 2  # preflight and the authoritative post-build decision


PROOF = REPO_ROOT / "infra/hetzner/proof/kill-switch-compose-proof.sh"


def test_compose_proof_is_disposable_only_and_covers_every_assumption() -> None:
    script = PROOF.read_text(encoding="utf-8")
    assert "if [[ -e /opt/la-lanh ]]; then" in script  # refuses a Lá Lành server
    assert 'PROJECT="la-lanh-killswitch-proof-$$"' in script  # never the production project
    for label in (
        "1. profiled worker survives",
        "2. rm -sf",
        "3. rm -sf with no worker",
        "4. LA_LANH",
    ):
        assert label in script
    assert subprocess.run(["/bin/bash", "-n", str(PROOF)], check=False).returncode == 0  # noqa: S603


@pytest.mark.skipif(shutil.which("docker") is None, reason="needs a disposable Docker host")
def test_real_compose_proof_on_a_disposable_host() -> None:
    """Runs only where Docker exists (never in this repo's CI); output is operator evidence."""

    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(PROOF)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
