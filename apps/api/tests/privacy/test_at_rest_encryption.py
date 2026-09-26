import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.domains.astro.models import TimePrecision, Tradition
from app.domains.birth.tables import BirthProfileRow
from app.domains.daily.models import DailyNoteRecord, PersonaLabel, PersonaMode, SourceLevel
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.tables import DailyNoteRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.models import (
    PlanMode,
    ReadingContentProjection,
    ReadingEvidenceProjection,
    ReadingPurpose,
    ReadingRevisionSource,
    ReadingSectionsProjection,
)
from app.domains.readings.tables import ReadingPlanRow, ReadingRevisionRow
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.postgres import PostgresSavedNoteRepository
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)


@pytest.fixture
async def storage(tmp_path: Path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'at-rest.db'}")
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(StaticDataKeyProvider(b"p" * 32))
    try:
        yield (
            database,
            PostgresDailyNoteRepository(database.sessions, envelope),
            PostgresSavedNoteRepository(database.sessions, envelope),
            PostgresShareArtifactRepository(database.sessions, envelope),
        )
    finally:
        await database.dispose()


async def _create_owner(database: Database) -> tuple[UUID, UUID]:
    guest_id = uuid4()
    profile_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest_id,
                token_hash=b"t" * 32,
                csrf_hash=b"c" * 32,
                state="active",
                onboarding_status="birth_ready",
                created_at=NOW,
                last_active_at=NOW,
                expires_at=NOW + timedelta(days=30),
            )
        )
        await session.flush()
        session.add(
            BirthProfileRow(
                id=profile_id,
                guest_id=guest_id,
                current_snapshot_id=None,
                profile_level=1,
                time_precision="unknown",
                created_at=NOW,
                updated_at=NOW,
            )
        )
    return guest_id, profile_id


def _daily_note(guest_id: UUID, *, note_id: UUID | None = None) -> DailyNoteRecord:
    return DailyNoteRecord(
        id=note_id or uuid4(),
        guest_id=guest_id,
        note_date=date(2026, 9, 7),
        title="DAILY_TITLE_CANARY",
        body="DAILY_BODY_CANARY",
        full_body="DAILY_FULL_BODY_CANARY",
        context_label="DAILY_CONTEXT_CANARY",
        content_version="daily-note-v3",
        persona_mode=PersonaMode.AURA,
        persona_label=PersonaLabel.DEEP,
        persona_version="persona-v2",
        source_level=SourceLevel.NATAL_CHART,
        astrology_source_version="swisseph-test",
        fallback_used=False,
        fallback_reason=None,
        chart_snapshot_id=None,
        created_at=NOW,
    )


def _reading(revision_id: UUID) -> ReadingContentProjection:
    return ReadingContentProjection(
        revision_id=revision_id,
        source=ReadingRevisionSource.DETERMINISTIC,
        mode=PlanMode.FULL_SYNTHESIS,
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        precision=TimePrecision.EXACT,
        sections=ReadingSectionsProjection(
            hook="READING_HOOK_CANARY",
            thesis="READING_THESIS_CANARY",
            manifestation="READING_MANIFESTATION_CANARY",
            transit="READING_TRANSIT_CANARY",
            micro_action="READING_ACTION_CANARY",
        ),
        evidence=ReadingEvidenceProjection(
            title="READING_EVIDENCE_TITLE_CANARY",
            claims=("PLACEMENT_MOON_HOUSE_CANARY",),
            framework_disclosure="READING_DISCLOSURE_CANARY",
        ),
        disclaimer="READING_DISCLAIMER_CANARY",
        created_at=NOW,
    )


async def _create_revision(database: Database, guest_id: UUID, profile_id: UUID) -> UUID:
    plan_id = uuid4()
    revision_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            ReadingPlanRow(
                id=plan_id,
                guest_id=guest_id,
                profile_id=profile_id,
                chart_snapshot_id=None,
                plan_key="a" * 64,
                plan_ciphertext="test-plan-ciphertext",
                created_at=NOW,
            )
        )
        await session.flush()
        session.add(
            ReadingRevisionRow(
                id=revision_id,
                guest_id=guest_id,
                profile_id=profile_id,
                plan_id=plan_id,
                revision_key="b" * 64,
                source="deterministic",
                renderer_version="renderer-test",
                content_version="content-test",
                schema_version="schema-test",
                rules_version="rules-test",
                gate_policy_version="gate-test",
                accepted=True,
                evaluation_ciphertext="test-evaluation-ciphertext",
                created_at=NOW,
            )
        )
    return revision_id


@pytest.mark.asyncio
async def test_new_records_encrypt_personalized_content_and_round_trip(storage) -> None:  # type: ignore[no-untyped-def]
    database, daily_repository, saved_repository, share_repository = storage
    guest_id, profile_id = await _create_owner(database)
    note = _daily_note(guest_id)
    stored_note = await daily_repository.get_or_create(note)
    assert stored_note == note
    assert await daily_repository.find(guest_id, note.id) == note
    refreshed_note = replace(
        note,
        id=uuid4(),
        title="DAILY_REFRESHED_TITLE_CANARY",
        content_version="daily-note-v4",
    )
    refreshed = await daily_repository.get_or_create(refreshed_note)
    assert refreshed.id == note.id
    assert refreshed.title == "DAILY_REFRESHED_TITLE_CANARY"
    assert await daily_repository.find(guest_id, note.id) == refreshed

    revision_id = await _create_revision(database, guest_id, profile_id)
    reading = _reading(revision_id)
    saved = SavedNoteRecord(
        id=uuid4(),
        guest_id=guest_id,
        daily_note_id=note.id,
        note_snapshot={"title": "SAVED_NOTE_CANARY", "body": "SAVED_BODY_CANARY"},
        profile_id=profile_id,
        revision_id=revision_id,
        reading_snapshot=reading,
        saved_at=NOW,
    )
    assert await saved_repository.save(saved) == saved
    assert await saved_repository.list_for_guest(guest_id) == (saved,)

    shared = ShareArtifactRecord(
        id=uuid4(),
        guest_id=guest_id,
        daily_note_id=note.id,
        token_hash=b"s" * 32,
        safe_snapshot=SafeShareSnapshot(
            title="SHARE_TITLE_CANARY",
            body="SHARE_BODY_CANARY",
            context_label="SHARE_CONTEXT_CANARY",
            content_version="daily-note-v3",
            persona_mode="aura",
            persona_label="Sâu",
            persona_version="persona-v2",
            watermark="Lá Lành",
        ),
        format=ShareFormat.STORY_9_16,
        created_at=NOW,
        expires_at=NOW + timedelta(days=14),
    )
    assert await share_repository.create(shared) == shared
    assert await share_repository.find_by_token_hash(shared.token_hash) == shared

    async with database.sessions() as session:
        daily_raw = (
            await session.execute(
                text(
                    "SELECT title, body, full_body, context_label, content_ciphertext "
                    "FROM daily_notes WHERE id = :id"
                ),
                {"id": note.id.hex},
            )
        ).one()
        saved_raw = (
            await session.execute(
                text(
                    "SELECT note_snapshot, reading_snapshot, snapshot_ciphertext "
                    "FROM saved_notes WHERE id = :id"
                ),
                {"id": saved.id.hex},
            )
        ).one()
        share_raw = (
            await session.execute(
                text(
                    "SELECT safe_snapshot, safe_snapshot_ciphertext "
                    "FROM share_artifacts WHERE id = :id"
                ),
                {"id": shared.id.hex},
            )
        ).one()

    assert tuple(daily_raw[:4]) == ("", "", "", "")
    assert json.loads(saved_raw.note_snapshot) == {}
    assert json.loads(saved_raw.reading_snapshot) == {}
    assert json.loads(share_raw.safe_snapshot) == {}
    ciphertexts = (
        daily_raw.content_ciphertext,
        saved_raw.snapshot_ciphertext,
        share_raw.safe_snapshot_ciphertext,
    )
    assert all(value.startswith("aesgcm:") for value in ciphertexts)
    raw_storage = " ".join(str(value) for row in (daily_raw, saved_raw, share_raw) for value in row)
    for canary in (
        "DAILY_TITLE_CANARY",
        "DAILY_REFRESHED_TITLE_CANARY",
        "DAILY_BODY_CANARY",
        "DAILY_FULL_BODY_CANARY",
        "DAILY_CONTEXT_CANARY",
        "SAVED_NOTE_CANARY",
        "SAVED_BODY_CANARY",
        "READING_HOOK_CANARY",
        "READING_THESIS_CANARY",
        "READING_MANIFESTATION_CANARY",
        "READING_TRANSIT_CANARY",
        "READING_ACTION_CANARY",
        "READING_EVIDENCE_TITLE_CANARY",
        "PLACEMENT_MOON_HOUSE_CANARY",
        "READING_DISCLOSURE_CANARY",
        "READING_DISCLAIMER_CANARY",
        "SHARE_TITLE_CANARY",
        "SHARE_BODY_CANARY",
        "SHARE_CONTEXT_CANARY",
    ):
        assert canary not in raw_storage


@pytest.mark.asyncio
async def test_legacy_plaintext_rows_remain_readable(storage) -> None:  # type: ignore[no-untyped-def]
    database, daily_repository, saved_repository, share_repository = storage
    guest_id, _ = await _create_owner(database)
    note_id = uuid4()
    saved_id = uuid4()
    share_id = uuid4()
    async with database.sessions() as session, session.begin():
        session.add(
            DailyNoteRow(
                id=note_id,
                guest_id=guest_id,
                note_date=date(2026, 9, 6),
                title="Legacy title",
                body="Legacy body",
                full_body="Legacy full body",
                context_label="Legacy context",
                content_ciphertext=None,
                content_version="daily-note-v2",
                persona_mode="vibe",
                persona_label="Mềm",
                persona_version="persona-v1",
                source_level="date_only_sun",
                astrology_source_version="legacy",
                fallback_used=True,
                fallback_reason="legacy_row",
                chart_snapshot_id=None,
                created_at=NOW,
            )
        )
        await session.flush()
        session.add(
            SavedNoteRow(
                id=saved_id,
                guest_id=guest_id,
                daily_note_id=note_id,
                note_snapshot={"title": "Legacy saved title"},
                snapshot_ciphertext=None,
                profile_id=None,
                revision_id=None,
                reading_snapshot=None,
                saved_at=NOW,
            )
        )
        session.add(
            ShareArtifactRow(
                id=share_id,
                guest_id=guest_id,
                daily_note_id=note_id,
                token_hash=b"l" * 32,
                safe_snapshot={
                    "title": "Legacy share title",
                    "body": "Legacy share body",
                    "context_label": "Legacy context",
                    "content_version": "daily-note-v2",
                    "persona_mode": "vibe",
                    "persona_label": "Mềm",
                    "persona_version": "persona-v1",
                    "watermark": "Lá Lành",
                },
                safe_snapshot_ciphertext=None,
                format="square_1_1",
                created_at=NOW,
                expires_at=NOW + timedelta(days=14),
                revoked_at=None,
            )
        )

    daily = await daily_repository.find(guest_id, note_id)
    saved = await saved_repository.list_for_guest(guest_id)
    shared = await share_repository.find_by_token_hash(b"l" * 32)
    assert daily is not None and daily.title == "Legacy title"
    assert saved[0].note_snapshot == {"title": "Legacy saved title"}
    assert shared is not None and shared.safe_snapshot.title == "Legacy share title"
