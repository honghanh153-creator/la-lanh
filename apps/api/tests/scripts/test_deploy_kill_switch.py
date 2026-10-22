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
PROOF_OPT_IN = "LA_LANH_KILL_SWITCH_PROOF"
PROOF_CONTEXT = "LA_LANH_PROOF_DOCKER_CONTEXT"
# Docker subcommands that create, change or delete state. A refused proof must not reach any.
STATEFUL = (" pull ", " tag ", " up ", " run ", " rm ", " image rm ", " down ")

FAKE_PROOF_DOCKER = r"""#!/usr/bin/env bash
# Records each call; answers only what the proof's guards ask. Never contacts Docker.
# The active context lives in $FAKE_ACTIVE so a test can switch it mid-run, as a concurrent
# `docker context use` in another terminal would. Each call also logs the daemon it would reach.
active() { cat "$FAKE_ACTIVE" 2>/dev/null || echo "${FAKE_CONTEXT:-disposable}"; }
if [[ -n "${DOCKER_HOST:-}" ]]; then target="$DOCKER_HOST"
elif [[ -n "${DOCKER_CONTEXT:-}" ]]; then target="context:$DOCKER_CONTEXT"
else target="context:$(active)"; fi
printf '%s\n' "$*" >> "$FAKE_LOG"
printf '%s|%s\n' "$target" "$*" >> "$FAKE_LOG.targets"
switch_after() { [[ "${FAKE_SWITCH_AFTER:-}" == "$1" ]] && echo production > "$FAKE_ACTIVE"; true; }
case " $* " in
  " context show ") active ;;
  " context inspect "*)
    echo "${FAKE_ENDPOINT:-unix:///var/run/docker.sock}"
    switch_after inspect ;;
  " info "*) exit "${FAKE_INFO_RC:-0}" ;;
  " ps -a "*) [[ -n "${FAKE_NAMES:-}" ]] && printf '%s\n' "$FAKE_NAMES"; switch_after ps; exit 0 ;;
  *) exit 0 ;;
esac
"""


def test_compose_proof_is_disposable_only_and_covers_every_assumption() -> None:
    script = PROOF.read_text(encoding="utf-8")
    assert "if [[ -e /opt/la-lanh ]]; then" in script  # refuses a Lá Lành server
    assert 'PROJECT="la-lanh-killswitch-proof-$RUN_ID"' in script  # never the production project
    for label in (
        "1. profiled worker survives",
        "2. rm -sf",
        "3. rm -sf with no worker",
        "4. LA_LANH",
    ):
        assert label in script
    assert subprocess.run(["/bin/bash", "-n", str(PROOF)], check=False).returncode == 0  # noqa: S603


def _proof(tmp_path: Path, **env: str) -> tuple[int, list[str], str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "docker").write_text(FAKE_PROOF_DOCKER)
    (bin_dir / "docker").chmod(0o755)
    log = tmp_path / "docker.log"
    log.write_text("")
    base = {
        "PATH": f"{bin_dir}{os.pathsep}/usr/bin:/bin",
        "FAKE_LOG": str(log),
        "FAKE_ACTIVE": str(tmp_path / "active-context"),
    }
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(PROOF)], env={**base, **env}, capture_output=True, text=True, check=False
    )
    return result.returncode, log.read_text().splitlines(), result.stdout + result.stderr


def _stateful(calls: list[str]) -> list[str]:
    return [call for call in calls if any(word in f" {call} " for word in STATEFUL)]


OPTED_IN = {PROOF_OPT_IN: "1", PROOF_CONTEXT: "disposable"}


def test_proof_without_opt_in_skips_before_touching_docker(tmp_path: Path) -> None:
    code, calls, output = _proof(tmp_path)
    assert code == 3, output
    assert calls == []
    assert PROOF_OPT_IN in output


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({**OPTED_IN, "DOCKER_HOST": "tcp://remote.invalid:2376"}, 4),
        ({**OPTED_IN, "DOCKER_CONTEXT": "disposable"}, 4),
        ({**OPTED_IN, "FAKE_ENDPOINT": "ssh://operator@remote.invalid"}, 4),
        ({**OPTED_IN, "FAKE_ENDPOINT": "tcp://10.0.0.5:2376"}, 4),
        ({**OPTED_IN, "FAKE_CONTEXT": "production"}, 4),
        ({PROOF_OPT_IN: "1"}, 4),
        ({**OPTED_IN, "FAKE_INFO_RC": "1"}, 5),
        ({**OPTED_IN, "FAKE_NAMES": "la-lanh-app-1"}, 2),
    ],
    ids=[
        "docker-host-env",
        "docker-context-env",
        "ssh-context",
        "tcp-context",
        "context-mismatch",
        "context-not-named",
        "daemon-unreachable",
        "la-lanh-containers-present",
    ],
)
def test_proof_refuses_unverified_docker_targets_without_changing_state(
    tmp_path: Path, env: dict[str, str], expected: int
) -> None:
    code, calls, output = _proof(tmp_path, **env)
    assert code == expected, output
    assert _stateful(calls) == []


def test_each_proof_run_uses_and_cleans_only_its_own_tags(tmp_path: Path) -> None:
    images: list[set[str]] = []
    for attempt in ("first", "second"):
        run_dir = tmp_path / attempt
        run_dir.mkdir()
        # The fake reports no running worker, so checks fail (exit 1); the tagging is what matters.
        code, calls, output = _proof(run_dir, **OPTED_IN)
        assert code == 1, output
        tagged = {call.split()[-1] for call in calls if call.startswith("tag busybox:1.36 ")}
        removed = next(call for call in calls if call.startswith("image rm ")).split()[2:]
        assert len(tagged) == 2 and set(removed) == tagged
        assert not any(name.startswith("busybox") for name in removed)
        images.append(tagged)
    assert images[0].isdisjoint(images[1])


@pytest.mark.parametrize("switch_after", ["inspect", "ps"])
def test_proof_stays_on_the_verified_target_after_the_active_context_changes(
    tmp_path: Path, switch_after: str
) -> None:
    """Another terminal runs `docker context use production` after the guard read the context."""
    _proof(tmp_path, **OPTED_IN, FAKE_SWITCH_AFTER=switch_after)
    verified = "unix:///var/run/docker.sock"
    calls = (tmp_path / "docker.log.targets").read_text().splitlines()
    inspected = next(i for i, line in enumerate(calls) if "|context inspect " in line)
    after_guard = calls[inspected + 1 :]
    assert after_guard, "the proof must keep running Docker commands after its guard"
    # Daemon probe, inventory, child shells and cleanup all reach the endpoint that was checked.
    assert all(line.split("|", 1)[0] == verified for line in after_guard), after_guard
    assert _stateful([line.split("|", 1)[1] for line in after_guard])
    assert not any(line.startswith("context:production|") for line in calls)


@pytest.mark.skipif(
    os.environ.get(PROOF_OPT_IN) != "1",
    reason=f"opt-in only: set {PROOF_OPT_IN}=1 and {PROOF_CONTEXT} on a disposable Docker host",
)
def test_real_compose_proof_on_a_disposable_host() -> None:
    """Runs only when an operator opts in on a disposable host; output is operator evidence."""

    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(PROOF)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
