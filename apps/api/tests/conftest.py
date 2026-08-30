from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


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
