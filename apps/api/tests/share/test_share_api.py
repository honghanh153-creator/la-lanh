from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes.guest_sessions import router as guest_router
from app.api.v1.routes.share_artifacts import router as share_router
from app.config import Settings
from app.domains.astro.models import TransitPhase
from app.domains.birth.errors import BirthProfileNotFound
from app.domains.daily.models import (
    AuraAwakening,
    DailyNoteRecord,
    PersonaLabel,
    PersonaMode,
    SkyChapter,
    SourceLevel,
)
from app.domains.guest.service import GuestSessionService
from app.domains.share.service import ShareArtifactService
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)
from tests.guest.test_guest_service import MemoryGuestRepository
from tests.share.test_share_service import MemoryShareRepository

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


def _test_app() -> tuple[FastAPI, MemoryGuestRepository, OwnedDailyNotes]:
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        cors_origins=[ORIGIN],
        guest_cookie_name=COOKIE_NAME,
        guest_cookie_secure=False,
    )
    guest_repository = MemoryGuestRepository()
    hasher = SecretHasher(decode_key(settings.guest_hash_key.get_secret_value()))
    envelope = AesGcmEnvelopeCipher(
        StaticDataKeyProvider(
            decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
        )
    )
    daily_notes = OwnedDailyNotes()
    app = FastAPI()
    app.state.settings = settings
    app.state.guest_session_service = GuestSessionService(
        guest_repository,
        hasher,
        envelope,
        consent_version=settings.consent_version,
        consent_purpose=settings.consent_purpose,
    )
    app.state.share_artifact_service = ShareArtifactService(MemoryShareRepository(), daily_notes)
    app.include_router(guest_router, prefix="/v1")
    app.include_router(share_router, prefix="/v1")
    return app, guest_repository, daily_notes


def _create_guest(
    client: TestClient,
    guest_repository: MemoryGuestRepository,
    idempotency_key: str,
) -> tuple[UUID, str, str]:
    existing_ids = {stored.guest.id for stored in guest_repository.guests.values()}
    response = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": idempotency_key,
        },
    )
    assert response.status_code == 200
    cookie = client.cookies.get(COOKIE_NAME)
    assert cookie is not None
    created_ids = {stored.guest.id for stored in guest_repository.guests.values()} - existing_ids
    assert len(created_ids) == 1
    return created_ids.pop(), cookie, response.json()["csrf_token"]


def _headers(csrf_token: str) -> dict[str, str]:
    return {"Origin": ORIGIN, "X-CSRF-Token": csrf_token}


def _create_owner_note(daily_notes: OwnedDailyNotes, guest_id: UUID) -> str:
    note = DailyNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 2),
        title="Safe title",
        body="Safe body",
        full_body="Safe full body",
        context_label="Safe context",
        content_version="daily-note-v1",
        persona_mode=PersonaMode.VIBE,
        persona_label=PersonaLabel.GROUNDED,
        persona_version="persona-v1",
        source_level=SourceLevel.DATE_ONLY_SUN,
        astrology_source_version="swisseph-v1",
        fallback_used=False,
        fallback_reason=None,
        chart_snapshot_id=uuid4(),
        created_at=datetime(2026, 9, 2, tzinfo=UTC),
        awakening=AuraAwakening(
            headline="PRIVATE_AURA_CANARY",
            summary="PRIVATE_AURA_SUMMARY_CANARY",
            factors=("PRIVATE_FACTOR_CANARY",),
            precision_label="PRIVATE_PRECISION_CANARY",
            scoring_version="PRIVATE_SCORING_CANARY",
            confidence="PRIVATE_CONFIDENCE_CANARY",
        ),
        sky_chapter=SkyChapter(
            title="PRIVATE_SKY_CANARY",
            summary="PRIVATE_TRANSIT_CANARY",
            phase=TransitPhase.EXACT,
            phase_label="PRIVATE_PHASE_CANARY",
            signal_label="PRIVATE_SIGNAL_CANARY",
            orb=0.01,
            observed_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
            orb_policy_version="transit-orbs-v1",
            ranking_version="sky-chapter-salience-v1",
            disclaimer="PRIVATE_DISCLAIMER_CANARY",
        ),
    )
    daily_notes.notes[note.id] = note
    return str(note.id)


def _assert_unavailable(response: Any) -> None:
    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "Share artifact is unavailable",
        "status": 404,
        "code": "SHARE_ARTIFACT_UNAVAILABLE",
    }


def test_share_create_and_revoke_are_owner_scoped_and_public_projection_is_safe() -> None:
    app, guest_repository, daily_notes = _test_app()
    with TestClient(app, base_url=ORIGIN) as client:
        owner_id, owner_cookie, owner_csrf = _create_guest(
            client, guest_repository, "share-owner-create-1234567890"
        )
        note_id = _create_owner_note(daily_notes, owner_id)
        created = client.post(
            f"/v1/daily-note/{note_id}/share-artifacts",
            json={"format": "story_9_16"},
            headers=_headers(owner_csrf),
        )
        assert created.status_code == 200
        artifact = created.json()
        token = artifact["token"]
        assert isinstance(token, str)
        assert len(token) >= 43
        assert artifact["expires_at"] > artifact["created_at"]

        public_path = f"/v1/share-artifacts/{token}"
        public = client.get(public_path)
        assert public.status_code == 200
        assert public.headers["cache-control"] == "no-store, max-age=0"
        assert public.headers["referrer-policy"] == "no-referrer"
        assert public.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
        assert set(public.json()) == {"format", "safe_snapshot", "expires_at"}
        assert set(public.json()["safe_snapshot"]) == {
            "title",
            "body",
            "context_label",
            "content_version",
            "persona_mode",
            "persona_label",
            "persona_version",
            "watermark",
        }
        serialized = str(public.json()).lower()
        for forbidden in (
            "birth_date",
            "birth_time",
            "birth_place",
            "latitude",
            "longitude",
            "guest_id",
            "daily_note_id",
            owner_cookie.lower(),
            owner_csrf.lower(),
            "private_",
        ):
            assert forbidden not in serialized

        _, _, other_csrf = _create_guest(client, guest_repository, "share-other-create-1234567890")
        cross_guest_create = client.post(
            f"/v1/daily-note/{note_id}/share-artifacts",
            json={"format": "square_1_1"},
            headers=_headers(other_csrf),
        )
        assert cross_guest_create.status_code == 404

        cross_guest_revoke = client.delete(
            f"/v1/share-artifacts/{artifact['id']}",
            headers=_headers(other_csrf),
        )
        _assert_unavailable(cross_guest_revoke)

        assert client.get(public_path).status_code == 200
        _assert_unavailable(client.get(f"/v1/share-artifacts/{artifact['id']}"))

        client.cookies.set(COOKIE_NAME, owner_cookie)
        revoked = client.delete(
            f"/v1/share-artifacts/{artifact['id']}",
            headers=_headers(owner_csrf),
        )
        assert revoked.status_code == 204
        assert revoked.content == b""

        revoked_public = client.get(public_path)
        unknown_public = client.get("/v1/share-artifacts/not-a-real-share-token")
        _assert_unavailable(revoked_public)
        _assert_unavailable(unknown_public)
        assert revoked_public.headers["cache-control"] == "no-store, max-age=0"
        assert unknown_public.headers["cache-control"] == "no-store, max-age=0"
        assert revoked_public.content == unknown_public.content


def test_revoke_requires_cookie_authentication_and_csrf() -> None:
    app, guest_repository, daily_notes = _test_app()
    with TestClient(app, base_url=ORIGIN) as client:
        guest_id, _, csrf = _create_guest(client, guest_repository, "share-auth-create-1234567890")
        note_id = _create_owner_note(daily_notes, guest_id)
        created = client.post(
            f"/v1/daily-note/{note_id}/share-artifacts",
            json={"format": "story_9_16"},
            headers=_headers(csrf),
        )
        artifact_id = created.json()["id"]

        no_csrf = client.delete(f"/v1/share-artifacts/{artifact_id}")
        assert no_csrf.status_code == 403

        client.cookies.clear()
        no_cookie = client.delete(f"/v1/share-artifacts/{artifact_id}", headers=_headers(csrf))
        assert no_cookie.status_code == 401
