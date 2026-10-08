from __future__ import annotations

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
    assert "LA_LANH_GUEST_HASH_KEY_FILE" not in worker
    assert "- guest_hash_key" not in worker
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
