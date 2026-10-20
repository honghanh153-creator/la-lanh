"""PR #38 review regressions: the 24-hour Daily window must not cascade children that have their
own unexpired contract, and expired history must never block today's note (real repositories)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import update

from app.db.session import Database
from app.domains.astro.engine import NatalChartEngine
from app.domains.birth.postgres import PostgresBirthRepository
from app.domains.daily.postgres import PostgresDailyNoteRepository
from app.domains.daily.tables import DailyNoteRow
from app.domains.experiments.postgres import PostgresExperimentRepository
from app.domains.experiments.tables import DailyExperimentRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.history.postgres import (
    DAILY_PURGE_WINDOW,
    PostgresHistoryRepository,
    activate_policy,
)
from app.domains.readings.application import ReadingApplicationService
from app.domains.readings.models import BackgroundLens, ReadingPurpose
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.tables import ReadingPlanRow, ReadingRevisionRow
from app.domains.resonance.models import ResonanceChoice
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.domains.resonance.service import ResonanceService
from app.domains.resonance.tables import ResonanceFeedbackRow
from app.domains.share.models import SafeShareSnapshot, ShareArtifactRecord, ShareFormat
from app.domains.share.postgres import PostgresShareArtifactRepository
from app.domains.share.tables import ShareArtifactRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider
from tests.experiments.test_postgres import NOW, ExperimentTarget, _choose, _create_target


def _cipher() -> AesGcmEnvelopeCipher:
    return AesGcmEnvelopeCipher(StaticDataKeyProvider(b"e" * 32))


@pytest.mark.asyncio
async def test_cleanup_keeps_a_hidden_daily_root_until_its_live_children_expire(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'synthetic-children.db'}")
    await database.initialize()
    try:
        envelope = _cipher()
        target = await _create_target(database, envelope)
        experiments = PostgresExperimentRepository(database.sessions, envelope)
        experiment = await _choose(experiments, target)
        share = await PostgresShareArtifactRepository(database.sessions, envelope).create(
            ShareArtifactRecord(
                id=uuid4(),
                guest_id=target.guest_id,
                daily_note_id=target.daily_note_id,
                token_hash=b"z" * 32,
                safe_snapshot=SafeShareSnapshot(*(["synthetic"] * 8)),
                format=ShareFormat.SQUARE_1_1,
                created_at=NOW,
                expires_at=NOW + timedelta(days=14),
            )
        )
        feedback = await ResonanceService(
            PostgresResonanceRepository(database.sessions, envelope)
        ).record(
            guest_id=target.guest_id,
            daily_note_id=target.daily_note_id,
            revision_id=target.revision_id,
            choice=ResonanceChoice.HIT,
            background_lens=BackgroundLens.WORK,
            consent_version="reading-resonance-v1",
            now=NOW,
        )
        async with database.sessions() as session, session.begin():
            await activate_policy(session, target.guest_id, NOW - timedelta(days=1))
        history = PostgresHistoryRepository(database.sessions, envelope)

        cleanup_at = NOW + DAILY_PURGE_WINDOW
        assert all(item.expires_at > cleanup_at for item in (experiment, share, feedback))
        await history.purge_expired(cleanup_at)
        async with database.sessions() as session:
            for model, item in (
                (DailyExperimentRow, experiment),
                (ShareArtifactRow, share),
                (ResonanceFeedbackRow, feedback),
            ):
                assert await session.get(model, item.id) is not None
            assert await session.get(DailyNoteRow, target.daily_note_id) is not None
        assert await experiments.current(target.guest_id, now=cleanup_at) is not None
        # The kept root is still hidden from the reader once past its 24-hour window.
        daily = PostgresDailyNoteRepository(database.sessions, envelope)
        assert await daily.find(target.guest_id, target.daily_note_id) is None

        # Once every child has expired, the next cleanup removes the root and its children.
        after = max(item.expires_at for item in (experiment, share, feedback)) + timedelta(
            seconds=1
        )
        for _ in range(5):
            if not await history.purge_expired(after):
                break
        async with database.sessions() as session:
            assert await session.get(DailyNoteRow, target.daily_note_id) is None
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_expired_yesterday_never_blocks_todays_rotated_note(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'synthetic-rotation.db'}")
    await database.initialize()
    try:
        cipher = _cipher()
        target = await _create_target(database, cipher)
        now = datetime.now(UTC)
        async with database.sessions() as session, session.begin():
            await session.execute(
                update(GuestSessionRow)
                .where(GuestSessionRow.id == target.guest_id)
                .values(expires_at=now + timedelta(days=30))
            )
        snapshot = await PostgresBirthRepository(database.sessions, cipher).find_current(
            target.guest_id
        )
        assert snapshot is not None
        service = ReadingApplicationService(
            PostgresReadingRepository(database.sessions, cipher),
            NatalChartEngine(),
            daily_variety_key=b"synthetic-only-key",
            daily_variety_from=date(2026, 1, 1),
        )
        await service.project(
            guest_id=target.guest_id,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
            requested_at=now - timedelta(hours=25),
        )
        async with database.sessions() as session, session.begin():
            await activate_policy(session, target.guest_id, now - timedelta(days=10))
        # Yesterday's projection is past its 24-hour window but not purged yet.
        today = await service.project(
            guest_id=target.guest_id,
            snapshot=snapshot,
            purpose=ReadingPurpose.DAILY_NOTE,
            requested_at=now,
        )
        assert today is not None
    finally:
        await database.dispose()


async def _revision_bound_share(
    tmp_path: Path, name: str
) -> tuple[Database, AesGcmEnvelopeCipher, ExperimentTarget, ShareArtifactRecord]:
    """A Daily target with only a revision-bound share: no experiment, no resonance feedback."""

    database = Database(f"sqlite+aiosqlite:///{tmp_path / name}")
    await database.initialize()
    envelope = _cipher()
    target = await _create_target(database, envelope)
    share = await PostgresShareArtifactRepository(database.sessions, envelope).create(
        ShareArtifactRecord(
            id=uuid4(),
            guest_id=target.guest_id,
            daily_note_id=target.daily_note_id,
            profile_id=target.profile_id,
            revision_id=target.revision_id,
            token_hash=b"r" * 32,
            safe_snapshot=SafeShareSnapshot(*(["synthetic"] * 8)),
            format=ShareFormat.SQUARE_1_1,
            created_at=NOW,
            expires_at=NOW + timedelta(days=14),
        )
    )
    async with database.sessions() as session, session.begin():
        await activate_policy(session, target.guest_id, NOW - timedelta(days=1))
    return database, envelope, target, share


async def _present(
    database: Database, target: ExperimentTarget, share: ShareArtifactRecord
) -> dict[str, bool]:
    async with database.sessions() as session:
        revision = await session.get(ReadingRevisionRow, target.revision_id)
        plan = await session.get(ReadingPlanRow, revision.plan_id) if revision is not None else None
        return {
            "root": await session.get(DailyNoteRow, target.daily_note_id) is not None,
            "revision": revision is not None,
            "plan": plan is not None,
            "share": await session.get(ShareArtifactRow, share.id) is not None,
        }


@pytest.mark.asyncio
async def test_live_revision_bound_share_alone_keeps_root_plan_revision_and_share(
    tmp_path: Path,
) -> None:
    database, envelope, target, share = await _revision_bound_share(tmp_path, "share-live.db")
    try:
        history = PostgresHistoryRepository(database.sessions, envelope)
        cleanup_at = NOW + DAILY_PURGE_WINDOW
        assert await history.remaining(cleanup_at) == 0
        assert await history.purge_expired(cleanup_at) == 0
        assert await history.remaining(cleanup_at) == 0
        assert await _present(database, target, share) == dict.fromkeys(
            ("root", "revision", "plan", "share"), True
        )
    finally:
        await database.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["revoked", "expired"])
async def test_revoked_or_expired_share_no_longer_keeps_the_daily_history(
    tmp_path: Path, ending: str
) -> None:
    database, envelope, target, share = await _revision_bound_share(tmp_path, f"share-{ending}.db")
    try:
        history = PostgresHistoryRepository(database.sessions, envelope)
        cleanup_at = NOW + DAILY_PURGE_WINDOW
        if ending == "revoked":
            assert await PostgresShareArtifactRepository(database.sessions, envelope).revoke_owned(
                target.guest_id, share.id, NOW + timedelta(hours=1)
            )
        else:
            cleanup_at = share.expires_at + timedelta(seconds=1)
        assert await history.remaining(cleanup_at) > 0
        for _ in range(5):
            if not await history.purge_expired(cleanup_at):
                break
        assert await history.remaining(cleanup_at) == 0
        assert await _present(database, target, share) == dict.fromkeys(
            ("root", "revision", "plan", "share"), False
        )
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_manual_clear_is_unchanged_by_the_live_share_exemption(tmp_path: Path) -> None:
    database, envelope, target, share = await _revision_bound_share(tmp_path, "share-manual.db")
    try:
        await PostgresHistoryRepository(database.sessions, envelope).clear(
            target.guest_id,
            NOW + DAILY_PURGE_WINDOW,
        )
        state = await _present(database, target, share)
        assert not state["root"] and not state["share"]
    finally:
        await database.dispose()
