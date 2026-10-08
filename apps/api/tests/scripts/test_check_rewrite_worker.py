from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from scripts import check_rewrite_worker as module


async def test_worker_healthcheck_requires_enabled_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "Settings", lambda: Settings(environment="test"))

    with pytest.raises(RuntimeError, match="disabled"):
        await module.check_rewrite_worker()


async def test_worker_healthcheck_probes_database_without_calling_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        generation_enabled=True,
        generation_worker_enabled=True,
        generation_provider="openai",
        generation_governance_approved=True,
        generation_spend_approved=True,
        generation_daily_token_budget=10_000,
        generation_daily_budget_cents=100,
        generation_surface_rollout={"daily_home": "shadow"},
        generation_openai_api_key="test-key",
    )
    database_check = AsyncMock()
    monkeypatch.setattr(module, "Settings", lambda: settings)
    monkeypatch.setattr(module, "check_database_tls", database_check)

    await module.check_rewrite_worker()

    database_check.assert_awaited_once_with()
