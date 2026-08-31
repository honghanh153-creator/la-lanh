from collections.abc import Iterator
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.birth.models import BirthSnapshotRecord
from app.main import create_app
from tests.guest.test_guest_service import MemoryGuestRepository


class MemoryBirthRepository:
    def __init__(self) -> None:
        self.current: dict[UUID, BirthSnapshotRecord] = {}
        self.by_input: dict[tuple[UUID, bytes], BirthSnapshotRecord] = {}

    async def save_or_replay(self, record: BirthSnapshotRecord) -> tuple[BirthSnapshotRecord, bool]:
        existing = self.by_input.get((record.guest_id, record.input_hash))
        if existing is not None:
            return existing, True
        current = self.current.get(record.guest_id)
        if current is not None:
            record = BirthSnapshotRecord(
                id=record.id,
                guest_id=record.guest_id,
                profile_id=current.profile_id,
                input_hash=record.input_hash,
                birth_date_ciphertext=record.birth_date_ciphertext,
                result=record.result,
                created_at=record.created_at,
            )
        self.current[record.guest_id] = record
        self.by_input[(record.guest_id, record.input_hash)] = record
        return record, False

    async def find_current(self, guest_id: UUID) -> BirthSnapshotRecord | None:
        return self.current.get(guest_id)


@pytest.fixture
def birth_repository() -> MemoryBirthRepository:
    return MemoryBirthRepository()


@pytest.fixture
def birth_client(birth_repository: MemoryBirthRepository) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://la_lanh:test@127.0.0.1:5432/la_lanh_test",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        ),
        guest_repository=MemoryGuestRepository(),
        birth_repository=birth_repository,
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        yield client


def create_guest(birth_client: TestClient) -> str:
    response = birth_client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "guest-create-key-1234567890",
        },
    )
    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    return str(payload["csrf_token"])


def test_birth_date_is_computed_by_real_engine_and_encrypted_at_rest(
    birth_client: TestClient,
    birth_repository: MemoryBirthRepository,
) -> None:
    csrf_token = create_guest(birth_client)
    response = birth_client.post(
        "/v1/birth-profile",
        json={"birth_date": "1990-01-01"},
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": csrf_token,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["calculation"]["status"] == "certain"
    assert payload["calculation"]["sign"] == "capricorn"
    assert payload["calculation"]["provenance"]["engine"] == "swiss_ephemeris"
    stored = next(iter(birth_repository.current.values()))
    assert "1990-01-01" not in stored.birth_date_ciphertext


def test_same_birth_input_replays_immutable_snapshot(birth_client: TestClient) -> None:
    csrf_token = create_guest(birth_client)
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "X-CSRF-Token": csrf_token,
    }
    first = birth_client.post(
        "/v1/birth-profile", json={"birth_date": "1990-01-01"}, headers=headers
    )
    second = birth_client.post(
        "/v1/birth-profile", json={"birth_date": "1990-01-01"}, headers=headers
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["snapshot_id"] == second.json()["snapshot_id"]
    assert second.json()["resumed"] is True


def test_birth_profile_resumes_from_guest_cookie(birth_client: TestClient) -> None:
    csrf_token = create_guest(birth_client)
    created = birth_client.post(
        "/v1/birth-profile",
        json={"birth_date": "1990-01-01"},
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": csrf_token,
        },
    )
    resumed = birth_client.get("/v1/birth-profile")
    assert resumed.status_code == 200
    assert resumed.json()["snapshot_id"] == created.json()["snapshot_id"]


def test_future_birth_date_is_rejected_without_snapshot(birth_client: TestClient) -> None:
    csrf_token = create_guest(birth_client)
    response = birth_client.post(
        "/v1/birth-profile",
        json={"birth_date": "2399-01-01"},
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": csrf_token,
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "BIRTH_DATE_OUT_OF_RANGE"
