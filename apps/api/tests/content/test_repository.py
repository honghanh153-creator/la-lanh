from copy import deepcopy
from pathlib import Path

import pytest

from app.db.session import Database
from app.domains.content.catalog import bundled_daily_catalog
from app.domains.content.postgres import ContentPublishConflict, PostgresContentRepository
from app.domains.content.validation import validate_daily_catalog


@pytest.mark.asyncio
async def test_draft_publish_and_stale_generation_conflict(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'content.db'}")
    await database.initialize()
    repository = PostgresContentRepository(database.sessions)
    try:
        payload = deepcopy(bundled_daily_catalog())
        payload["signs"]["pisces"]["hooks"][0] = (
            "Bạn đã thấy không khí đổi trước khi cuộc trò chuyện gọi tên điều đó."
        )
        revision = await repository.create_draft(
            payload,
            parent_revision_id=None,
            request_key="draft-1",
            reason="Clarify a novice-facing Pisces hook",
        )
        receipt = validate_daily_catalog(payload)
        assert receipt.passed is True
        validated = await repository.record_validation(
            revision.id,
            receipt,
            request_key="validate-1",
            reason="Automated validation",
        )
        published, channel = await repository.activate(
            validated.id,
            expected_generation=0,
            request_key="publish-1",
            reason="Approved for local review",
        )

        assert published.status.value == "published"
        assert channel.active_revision_id == published.id
        assert channel.generation == 1
        replayed, replayed_channel = await repository.activate(
            published.id,
            expected_generation=0,
            request_key="publish-1",
            reason="Idempotent retry",
        )
        assert replayed.id == published.id
        assert replayed_channel.generation == 1
        with pytest.raises(ContentPublishConflict):
            await repository.activate(
                published.id,
                expected_generation=0,
                request_key="publish-stale",
                reason="Stale publish",
            )
        still_published = await repository.get_revision(published.id)
        assert still_published is not None
        assert still_published.status.value == "published"

        stale_payload = deepcopy(payload)
        stale_payload["signs"]["pisces"]["hooks"][0] = (
            "Draft này được tạo từ một parent đã cũ nên không được ghi đè release mới."
        )
        stale = await repository.create_draft(
            stale_payload,
            parent_revision_id=None,
            request_key="draft-stale-parent",
            reason="Exercise parent compare-and-swap",
        )
        stale = await repository.record_validation(
            stale.id,
            validate_daily_catalog(stale_payload),
            request_key="validate-stale-parent",
            reason="Validate stale-parent draft",
        )
        with pytest.raises(ContentPublishConflict):
            await repository.activate(
                stale.id,
                expected_generation=1,
                request_key="publish-stale-parent",
                reason="Must not overwrite newer release",
            )
        with pytest.raises(ContentPublishConflict):
            await repository.activate(
                stale.id,
                expected_generation=1,
                request_key="rollback-never-published",
                reason="Must not label a draft as rollback",
                rollback=True,
            )
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_same_payload_replays_one_revision(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'replay.db'}")
    await database.initialize()
    repository = PostgresContentRepository(database.sessions)
    try:
        payload = bundled_daily_catalog()
        first = await repository.create_draft(
            payload,
            parent_revision_id=None,
            request_key="draft-first",
            reason="Create baseline",
        )
        replay = await repository.create_draft(
            payload,
            parent_revision_id=None,
            request_key="draft-replay",
            reason="Replay baseline",
        )

        assert replay.id == first.id
        assert len(await repository.list_revisions()) == 1
    finally:
        await database.dispose()
