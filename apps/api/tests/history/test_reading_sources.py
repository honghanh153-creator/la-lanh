from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.session import Database
from app.domains.astro.engine import NatalChartEngine
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.history.errors import HistoryUnavailable
from app.domains.history.postgres import PostgresHistoryRepository, activate_policy
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.models import BackgroundLens, ReadingPurpose
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.tables import ReadingPlanRow, ReadingRevisionRow
from app.domains.saved.models import SavedNoteRecord
from app.domains.saved.postgres import PostgresSavedNoteRepository
from tests.experiments.test_postgres import NOW as SOURCE_TIME
from tests.experiments.test_postgres import _create_target
from tests.history.test_retention import NOW, OLD, cipher
from tests.readings.test_revision_repository import _plan_record, _revision_record


async def test_expired_daily_scope_and_revision_unavailable_before_purge(storage: Database) -> None:
    target = await _create_target(storage, cipher())
    readings = PostgresReadingRepository(storage.sessions, cipher())
    application = ReadingApplicationService(readings, NatalChartEngine())
    snapshot = await PostgresBirthRepository(storage.sessions, cipher()).find_current(
        target.guest_id
    )
    assert snapshot is not None
    projection = await application.project(
        guest_id=target.guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=SOURCE_TIME,
        background_lens=BackgroundLens.WORK,
    )
    async with storage.sessions() as session, session.begin():
        await activate_policy(session, target.guest_id, OLD)
    with pytest.raises(HistoryUnavailable):
        await readings.get_projection(target.guest_id, target.profile_id, projection.scope_key)
    assert (
        await readings.get_revision(target.guest_id, target.profile_id, target.revision_id) is None
    )
    with pytest.raises(HistoryUnavailable):
        await readings.activate_available(
            target.guest_id,
            target.profile_id,
            projection.scope_key,
            expected_revision_id=target.revision_id,
            updated_at=NOW,
        )
    async with storage.sessions() as session:
        assert await session.get(ReadingRevisionRow, target.revision_id) is not None


async def test_clear_preserves_precise_chart_saved_revision_current_and_nondaily_pointers(
    storage: Database,
) -> None:
    target = await _create_target(storage, cipher())
    other = await _create_target(storage, cipher())
    readings = PostgresReadingRepository(storage.sessions, cipher())
    application = ReadingApplicationService(readings, NatalChartEngine())
    snapshot = await PostgresBirthRepository(storage.sessions, cipher()).find_current(
        target.guest_id
    )
    assert snapshot is not None
    historical = await application.project(
        guest_id=target.guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=SOURCE_TIME,
        background_lens=BackgroundLens.WORK,
    )
    frozen = await PostgresSavedNoteRepository(storage.sessions, cipher()).save(
        SavedNoteRecord(
            id=uuid4(),
            guest_id=target.guest_id,
            daily_note_id=target.daily_note_id,
            note_snapshot={"body": "explicitly saved"},
            saved_at=NOW,
            profile_id=target.profile_id,
            revision_id=target.revision_id,
            reading_snapshot=historical.active,
        )
    )
    current = await application.project(
        guest_id=target.guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.DAILY_NOTE,
        requested_at=NOW,
    )
    insight = await application.project(
        guest_id=target.guest_id,
        snapshot=snapshot,
        purpose=ReadingPurpose.AURA,
        requested_at=SOURCE_TIME,
    )
    orphan_plan, _ = await readings.save_or_replay_plan(
        _plan_record(target.guest_id, target.profile_id)
    )
    orphan_revision, _ = await readings.save_or_replay_revision(_revision_record(orphan_plan))
    async with storage.sessions() as session, session.begin():
        guest = await session.get(GuestSessionRow, target.guest_id)
        assert guest is not None
        guest.expires_at = NOW + timedelta(days=365)
        await activate_policy(session, target.guest_id, OLD)
        session.add(
            ConsentRow(
                guest_id=target.guest_id, purpose="synthetic", version="test", accepted_at=NOW
            )
        )
        before = await session.scalar(
            select(ChartSnapshotRow.result_ciphertext).where(
                ChartSnapshotRow.id == target.snapshot.id
            )
        )
    await PostgresHistoryRepository(storage.sessions, cipher()).clear(target.guest_id, NOW)
    assert await PostgresSavedNoteRepository(storage.sessions, cipher()).list_for_guest(
        target.guest_id
    ) == (frozen,)
    assert await readings.get_projection(target.guest_id, target.profile_id, current.scope_key)
    assert await readings.get_projection(target.guest_id, target.profile_id, insight.scope_key)
    async with storage.sessions() as session:
        profile = await session.get(BirthProfileRow, target.profile_id)
        chart = await session.get(ChartSnapshotRow, target.snapshot.id)
        assert profile is not None and profile.current_snapshot_id == target.snapshot.id
        assert chart is not None and chart.result_ciphertext == before
        assert await session.get(ReadingRevisionRow, target.revision_id) is not None
        assert await session.get(ReadingRevisionRow, other.revision_id) is not None
        current_revision = await session.get(ReadingRevisionRow, current.active.revision_id)
        assert current_revision is not None
        assert await session.get(ReadingPlanRow, current_revision.plan_id) is not None
        assert await session.get(ReadingPlanRow, orphan_plan.id) is None
        assert await session.get(ReadingRevisionRow, orphan_revision.id) is None
        assert (
            await session.scalar(
                select(ConsentRow.id).where(
                    ConsentRow.guest_id == target.guest_id, ConsentRow.purpose == "synthetic"
                )
            )
            is not None
        )
