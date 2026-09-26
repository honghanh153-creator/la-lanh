from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes.guest_sessions import router as guest_router
from app.api.v1.routes.saved_notes import router as saved_router
from app.config import Settings
from app.domains.birth.errors import BirthProfileNotFound
from app.domains.daily.models import DailyNoteRecord
from app.domains.guest.service import GuestSessionService
from app.domains.saved.service import SavedNoteService
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)
from tests.guest.test_guest_service import MemoryGuestRepository
from tests.saved.test_saved_service import MemorySavedRepository

ORIGIN = "http://127.0.0.1:5173"
COOKIE_NAME = "la_lanh_guest"


class OwnedDailyNotes:
    def __init__(self) -> None:
        self.notes: dict[UUID, DailyNoteRecord] = {}

    async def find_owned(self, guest_id: UUID, note_id: UUID) -> DailyNoteRecord:
        note = self.notes.get(note_id)
        if note is None or note.guest_id != guest_id:
            raise BirthProfileNotFound
        return note


def _app() -> tuple[FastAPI, MemoryGuestRepository, OwnedDailyNotes]:
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        cors_origins=[ORIGIN],
        guest_cookie_name=COOKIE_NAME,
        guest_cookie_secure=False,
    )
    guests = MemoryGuestRepository()
    notes = OwnedDailyNotes()
    hasher = SecretHasher(decode_key(settings.guest_hash_key.get_secret_value()))
    envelope = AesGcmEnvelopeCipher(
        StaticDataKeyProvider(
            decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
        )
    )
    app = FastAPI()
    app.state.settings = settings
    app.state.guest_session_service = GuestSessionService(
        guests,
        hasher,
        envelope,
        consent_version=settings.consent_version,
        consent_purpose=settings.consent_purpose,
    )
    app.state.saved_note_service = SavedNoteService(MemorySavedRepository(), notes)
    app.state.reading_application_service = None
    app.include_router(guest_router, prefix="/v1")
    app.include_router(saved_router, prefix="/v1")
    return app, guests, notes


def _create_guest(client: TestClient, guests: MemoryGuestRepository, key: str) -> tuple[UUID, str]:
    before = {stored.guest.id for stored in guests.guests.values()}
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": key,
        },
    )
    assert response.status_code == 200
    created = {stored.guest.id for stored in guests.guests.values()} - before
    assert len(created) == 1
    return created.pop(), str(response.json()["csrf_token"])


def _note(guest_id: UUID) -> DailyNoteRecord:
    return DailyNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 7),
        title="Owned note",
        body="Only its owner may save this.",
        context_label="Vibe",
        content_version="daily-note-v3",
        chart_snapshot_id=None,
        created_at=datetime(2026, 9, 7, tzinfo=UTC),
    )


def _headers(csrf: str) -> dict[str, str]:
    return {"Origin": ORIGIN, "X-CSRF-Token": csrf}


def test_saved_mutations_require_csrf_and_do_not_cross_guest_ownership() -> None:
    app, guests, notes = _app()
    with TestClient(app, base_url=ORIGIN) as client:
        owner_id, owner_csrf = _create_guest(client, guests, "saved-owner-123456789012345")
        note = _note(owner_id)
        notes.notes[note.id] = note

        assert client.put(f"/v1/daily-note/{note.id}/saved").status_code == 403
        saved = client.put(f"/v1/daily-note/{note.id}/saved", headers=_headers(owner_csrf))
        assert saved.status_code == 200
        assert saved.json()["revision_id"] is None

        _, other_csrf = _create_guest(client, guests, "saved-other-123456789012345")
        cross_owner = client.put(
            f"/v1/daily-note/{note.id}/saved",
            headers=_headers(other_csrf),
        )
        assert cross_owner.status_code == 404

        other_list: list[dict[str, Any]] = client.get("/v1/saved-notes").json()
        assert other_list == []
