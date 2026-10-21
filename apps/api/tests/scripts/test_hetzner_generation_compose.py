from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def _service_section(compose: str, name: str, next_name: str) -> str:
    return compose.split(f"  {name}:\n", 1)[1].split(f"  {next_name}:\n", 1)[0]


def test_api_and_worker_receive_only_their_required_secrets() -> None:
    compose = (REPO_ROOT / "infra/hetzner/compose.yaml").read_text(encoding="utf-8")
    app = _service_section(compose, "app", "rewrite-worker")
    worker = _service_section(compose, "rewrite-worker", "caddy")

    assert "LA_LANH_GUEST_HASH_KEY_FILE" in app
    assert "LA_LANH_GENERATION_OPENAI_API_KEY_FILE" not in app
    # The worker uses the same production Settings contract as the API. It must
    # start with a managed hash key; the API still must not receive a provider key.
    assert "LA_LANH_GUEST_HASH_KEY_FILE: /run/secrets/guest_hash_key" in worker
    assert "- guest_hash_key" in worker
    assert "LA_LANH_GENERATION_OPENAI_API_KEY_FILE" in worker
    assert "- openai_api_key" in worker
    assert "healthcheck:" in worker
    assert "scripts.check_rewrite_worker" in worker


def test_deploy_uses_application_settings_for_generation_profile_selection() -> None:
    deploy = (REPO_ROOT / "infra/hetzner/deploy.sh").read_text(encoding="utf-8")

    assert "Settings().generation_enabled" in deploy
    assert "COMPOSE_PROFILES=generation" in deploy
    assert 'require_secret_file "${LA_LANH_SECRETS_DIR}/openai_api_key"' in deploy
    assert "grep -Eq '^LA_LANH_GENERATION_ENABLED=true$'" not in deploy


def test_worker_entrypoint_satisfies_production_settings_with_fake_mounted_secrets(
    tmp_path: Path,
) -> None:
    env = {
        "PATH": os.environ["PATH"],
        "LA_LANH_ENVIRONMENT": "production",
        "LA_LANH_SWISSEPH_LICENSE_MODE": "agpl",
        "LA_LANH_GUEST_COOKIE_SECURE": "true",
        "LA_LANH_CORS_ORIGINS": '["https://synthetic.invalid"]',
        "LA_LANH_GENERATION_ENABLED": "true",
        "LA_LANH_GENERATION_WORKER_ENABLED": "true",
        "LA_LANH_GENERATION_PROVIDER": "openai",
        "LA_LANH_GENERATION_GOVERNANCE_APPROVED": "true",
        "LA_LANH_GENERATION_SPEND_APPROVED": "true",
        "LA_LANH_GENERATION_DAILY_TOKEN_BUDGET": "1000",
        "LA_LANH_GENERATION_DAILY_BUDGET_CENTS": "3",
        "LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS": "90",
        "LA_LANH_GENERATION_PILOT_USER_LIMIT": "20",
        "LA_LANH_GENERATION_OPENAI_PROJECT_ID": "proj_synthetic",
        "LA_LANH_GENERATION_SURFACE_ROLLOUT": '{"daily_home":"full"}',
        "LA_LANH_AUTH_ENABLED": "true",
        "LA_LANH_AUTH_GOOGLE_ENABLED": "true",
        "LA_LANH_AUTH_DELIVERY_APPROVED": "true",
    }
    # Apply the actual worker overrides, not an idealized Settings fixture.
    compose = (REPO_ROOT / "infra/hetzner/compose.yaml").read_text()
    worker = _service_section(compose, "rewrite-worker", "caddy")
    for flag in ("AUTH_ENABLED", "AUTH_GOOGLE_ENABLED", "AUTH_DELIVERY_APPROVED"):
        if f'LA_LANH_{flag}: "false"' in worker:
            env[f"LA_LANH_{flag}"] = "false"
    for variable, value in (
        ("DATABASE_URL", "postgresql+asyncpg://synthetic:fake@127.0.0.1/synthetic"),
        ("GUEST_HASH_KEY", "synthetic-managed-hash-not-the-development-default"),
        ("GUEST_ENCRYPTION_KEY", "synthetic-managed-encryption-not-a-real-key"),
        ("GENERATION_OPENAI_API_KEY", "synthetic-provider-key-never-used"),
    ):
        path = tmp_path / variable
        path.write_text(value)
        env[f"LA_LANH_{variable}_FILE"] = str(path)
    # Arguments are fixed repository code and fake fixtures, never user input.
    result = subprocess.run(  # noqa: S603
        [
            "/bin/sh",
            str(REPO_ROOT / "infra/hetzner/entrypoint.sh"),
            sys.executable,
            "-c",
            "from app.config import Settings; "
            "s=Settings(_env_file=None); assert s.generation_worker_enabled; "
            "assert not s.auth_enabled and not s.auth_google_enabled; print('settings-ok')",
        ],
        env=env,
        cwd=REPO_ROOT / "apps/api",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "settings-ok"
    assert result.stderr == ""


def test_deploy_and_cleanup_use_same_admin_secret_selection(tmp_path: Path) -> None:
    infra = REPO_ROOT / "infra/hetzner"
    selector = infra / "compose-files.sh"
    assert selector.exists()
    env_dir = tmp_path / "infra"
    env_dir.mkdir()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    for enabled, present, expected in (
        ("true", False, 2),
        ("true", True, 0),
        ("false", True, 0),
        ("false", False, 0),
    ):
        (env_dir / "app.env").write_text(f"LA_LANH_AUTH_ENABLED={enabled}\n")
        secret = secrets / "supabase_admin_key"
        if present:
            secret.write_text("synthetic-only-not-a-real-key")
        else:
            secret.unlink(missing_ok=True)
        result = subprocess.run(  # noqa: S603
            [
                "/bin/bash",
                "-ec",
                'source "$1"; require_secret_file() { test -s "$1"; }; '
                'select_compose_files "$2"; printf "%s\\n" "${COMPOSE_ARGS[@]}"',
                "test",
                str(selector),
                str(env_dir),
            ],
            env={"PATH": os.environ["PATH"], "LA_LANH_SECRETS_DIR": str(secrets)},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == expected
        if expected == 0:
            assert ("compose.auth.yaml" in result.stdout) is present
    for script in ("deploy.sh", "run-retention-job.sh"):
        assert "select_compose_files" in (infra / script).read_text()
    assert "/usr/local/sbin/la-lanh-retention-job" in (infra / "deploy.sh").read_text()


def test_staging_worker_mirrors_production_and_is_the_only_key_holder() -> None:
    compose = (REPO_ROOT / "infra/hetzner/staging/compose.staging.yaml").read_text()
    app = _service_section(compose, "staging-app", "staging-rewrite-worker")
    worker = compose.split("  staging-rewrite-worker:\n", 1)[1].split("\nnetworks:\n", 1)[0]

    assert "openai_api_key" not in app
    assert 'LA_LANH_GENERATION_WORKER_ENABLED: "false"' in app
    assert "profiles:\n      - generation" in worker
    assert "LA_LANH_GENERATION_OPENAI_API_KEY_FILE: /run/secrets/openai_api_key" in worker
    assert 'LA_LANH_GENERATION_WORKER_ENABLED: "true"' in worker
    assert "- openai_api_key" in worker
    assert "scripts.check_rewrite_worker" in worker
    # Own egress only: never on the shared production network, never named like prod.
    assert "edge" not in worker
    assert "worker-egress: {}" in worker
    assert "\n  rewrite-worker:\n" not in compose
    assert "\n  app:\n" not in compose
    production = _service_section(
        (REPO_ROOT / "infra/hetzner/compose.yaml").read_text(), "rewrite-worker", "caddy"
    )
    for line in (
        "read_only: true",
        "no-new-privileges:true",
        "- ALL",
        'LA_LANH_AUTH_ENABLED: "false"',
        'command: ["python", "-m", "app.domains.content_rewrite.worker"]',
    ):
        assert line in production and line in worker


def test_staging_up_defaults_generation_off_and_never_inherits_production_values(
    tmp_path: Path,
) -> None:
    up = (REPO_ROOT / "infra/hetzner/staging/up.sh").read_text()
    assert "${STAGING_GENERATION:-off}" in up
    assert "grep -v '^LA_LANH_GENERATION_'" in up
    assert 'echo "LA_LANH_GENERATION_ENABLED=false" >> "$HERE/app.env"' in up
    assert "OPENAI_API_KEY|OPENAI_API_KEY_FILE|WORKER_ENABLED" in up
    assert "rm -sf staging-rewrite-worker" in up
    # Exercise the same filter the script uses on a synthetic production env.
    source = tmp_path / "app.env"
    source.write_text(
        "LA_LANH_ENVIRONMENT=production\n"
        "LA_LANH_GENERATION_ENABLED=true\n"
        'LA_LANH_GENERATION_SURFACE_ROLLOUT={"daily_home":"full"}\n'
    )
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", "-c", "{ grep -v '^LA_LANH_GENERATION_' \"$1\" || true; }", "_", str(source)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "LA_LANH_ENVIRONMENT=production\n"
