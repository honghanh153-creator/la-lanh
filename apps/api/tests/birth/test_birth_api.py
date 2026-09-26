from collections.abc import Iterator
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.birth.models import BirthSnapshotRecord, BirthSupplement, BirthSupplementStored
from app.main import create_app
from tests.guest.test_guest_service import MemoryGuestRepository


class MemoryBirthRepository:
    def __init__(self) -> None:
        self.current: dict[UUID, BirthSnapshotRecord] = {}
        self.by_input: dict[tuple[UUID, bytes], BirthSnapshotRecord] = {}
        self.supplements: dict[UUID, BirthSupplementStored] = {}

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

    async def find_by_input_hash(
        self, guest_id: UUID, input_hash: bytes
    ) -> BirthSnapshotRecord | None:
        return self.by_input.get((guest_id, input_hash))

    async def save_supplement(
        self,
        guest_id: UUID,
        snapshot: BirthSnapshotRecord | None,
        supplement: BirthSupplement,
    ) -> BirthSnapshotRecord | None:
        if snapshot is not None:
            self.current[guest_id] = snapshot
            self.by_input[(guest_id, snapshot.input_hash)] = snapshot
        current = self.current[guest_id]
        self.supplements[guest_id] = BirthSupplementStored(
            profile_id=current.profile_id,
            profile_level=(
                3 if supplement.birth_place_ciphertext and supplement.birth_time_ciphertext else 2
            ),
            birth_time_ciphertext=supplement.birth_time_ciphertext,
            birth_place_ciphertext=supplement.birth_place_ciphertext,
            time_precision=supplement.birth_time_mode.value,
            supplement_consent_version=supplement.consent_version,
        )
        return snapshot

    async def find_supplement(self, guest_id: UUID) -> BirthSupplementStored | None:
        return self.supplements.get(guest_id)

    async def clear_supplement(
        self, guest_id: UUID, *, remove_time: bool, remove_place: bool
    ) -> BirthSupplementStored:
        stored = self.supplements[guest_id]
        updated = BirthSupplementStored(
            profile_id=stored.profile_id,
            profile_level=1 if remove_time else 2,
            birth_time_ciphertext=None if remove_time else stored.birth_time_ciphertext,
            birth_place_ciphertext=None if remove_place else stored.birth_place_ciphertext,
            time_precision="unknown" if remove_time else stored.time_precision,
            supplement_consent_version=stored.supplement_consent_version,
        )
        self.supplements[guest_id] = updated
        return updated


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
    assert payload["calculation_kind"] == "date_only_sun"
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

    def fail_if_recomputed(_birth_date) -> None:  # type: ignore[no-untyped-def]
        raise AssertionError("replayed input must not enter Swiss Ephemeris")

    app = cast(FastAPI, birth_client.app)
    app.state.birth_chart_service._engine.calculate_date_only_sun = fail_if_recomputed
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


@pytest.mark.parametrize("birth_date", ["2010-01-01", "1800-01-01"])
def test_age_policy_rejects_under_18_and_over_120(
    birth_client: TestClient,
    birth_date: str,
) -> None:
    csrf_token = create_guest(birth_client)
    response = birth_client.post(
        "/v1/birth-profile",
        json={"birth_date": birth_date},
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": csrf_token,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "BIRTH_DATE_OUT_OF_RANGE"
