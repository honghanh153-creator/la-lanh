from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def stored_private_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Owner AP2 (21.11.2026) retired self-attested private checks for users. Tests still build
    results through that path, so they turn it on; tests about the retirement pass
    ``radar_self_attested_checks=False`` explicitly."""

    monkeypatch.setenv("LA_LANH_RADAR_SELF_ATTESTED_CHECKS", "true")


@pytest.fixture
def test_app() -> FastAPI:
    return create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://la_lanh:test@127.0.0.1:5432/la_lanh_test",
        )
    )


@pytest.fixture
def client(test_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def frozen_admission_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep every request of a rate-limit test in one admission window.

    The admission windows are fixed minutes of time.monotonic(). A burst that crossed a minute
    boundary started a fresh count, so "the 6th export is refused" failed on a slow CI run
    (PR #354, 15.11.2026). Only the admission module's clock is frozen.
    """

    from app.middleware import admission

    monkeypatch.setattr(admission, "time", SimpleNamespace(monotonic=lambda: 1_000_020.0))
