"""The proposed daily_home pilot config in the runbook must pass the real validators."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.config import Settings
from app.domains.content_rewrite.models import RewriteSurface
from app.domains.content_rewrite.rollout import RewriteRolloutMode, SurfaceRolloutPolicy

REPO_ROOT = Path(__file__).resolve().parents[4]
RUNBOOK = REPO_ROOT / "docs/operations/luna-rewrite-release-runbook.md"
_USER_VISIBLE = {"beta_10", "beta_50", "full"}


def _block(label: str) -> dict[str, str]:
    text = RUNBOOK.read_text(encoding="utf-8")
    match = re.search(rf"```text {label}\n(.*?)```", text, flags=re.DOTALL)
    assert match is not None, label
    pairs = [line.split("=", 1) for line in match.group(1).splitlines() if line.strip()]
    return {key: value for key, value in pairs}


@pytest.mark.parametrize("label", ["pilot-staging", "pilot-production"])
def test_proposed_pilot_config_passes_worker_settings_with_fake_secrets(
    label: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _block(label)
    assert not any("API_KEY" in key or "WORKER_ENABLED" in key for key in values)
    assert all(key.startswith("LA_LANH_GENERATION_") for key in values)
    for key in list(Settings.model_fields):
        monkeypatch.delenv(f"LA_LANH_{key.upper()}", raising=False)
    base = {
        "LA_LANH_ENVIRONMENT": "production",
        "LA_LANH_SWISSEPH_LICENSE_MODE": "agpl",
        "LA_LANH_GUEST_COOKIE_SECURE": "true",
        "LA_LANH_CORS_ORIGINS": '["https://synthetic.invalid"]',
        "LA_LANH_DATABASE_URL": "postgresql+asyncpg://synthetic:fake@127.0.0.1/synthetic",
        "LA_LANH_GUEST_HASH_KEY": "synthetic-managed-hash-not-the-development-default",
        "LA_LANH_GUEST_ENCRYPTION_KEY": "synthetic-managed-encryption-not-a-real-key",
        # Compose sets these two inside the worker only.
        "LA_LANH_GENERATION_WORKER_ENABLED": "true",
        "LA_LANH_GENERATION_OPENAI_API_KEY": "synthetic-provider-key-never-used",
    }
    for key, value in {**base, **values}.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.generation_enabled and settings.generation_worker_enabled
    assert settings.generation_spend_approved and settings.generation_governance_approved
    assert settings.generation_surface_rollout == {"daily_home": "full"}
    assert settings.generation_surface_rollout["daily_home"] in _USER_VISIBLE
    policy = SurfaceRolloutPolicy.from_settings(settings.generation_surface_rollout)
    assert policy.mode_for(RewriteSurface.DAILY_HOME) is RewriteRolloutMode.FULL
    for surface in RewriteSurface:
        if surface is not RewriteSurface.DAILY_HOME:
            assert not policy.should_generate(surface), surface
    assert 1 <= settings.generation_pilot_user_limit <= 20
    assert settings.generation_daily_budget_cents == 3
    assert settings.generation_daily_token_budget == 300_000


def test_staging_and_production_monthly_caps_fit_the_owner_total() -> None:
    staging = _block("pilot-staging")
    production = _block("pilot-production")
    assert production["LA_LANH_GENERATION_PILOT_USER_LIMIT"] == "20"
    total = int(staging["LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS"]) + int(
        production["LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS"]
    )
    assert total <= 90
    assert json.loads(staging["LA_LANH_GENERATION_SURFACE_ROLLOUT"]) == json.loads(
        production["LA_LANH_GENERATION_SURFACE_ROLLOUT"]
    )
