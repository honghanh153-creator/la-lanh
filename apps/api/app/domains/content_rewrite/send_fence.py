import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.tables import RewriteSendFenceRow

SendTokens = tuple[tuple[UUID, UUID], ...]


async def pending_sends(
    session: AsyncSession, subjects: tuple[UUID, ...], *, job_ids: tuple[UUID, ...] | None = None
) -> SendTokens:
    """Capture under owner/parent locks, before consent withdrawal or source erasure."""
    query = select(RewriteSendFenceRow.job_id, RewriteSendFenceRow.lease_token).where(
        RewriteSendFenceRow.subject_id.in_(subjects)
    )
    if job_ids is not None:
        query = query.where(RewriteSendFenceRow.job_id.in_(job_ids))
    rows = await session.execute(query.distinct())
    return tuple((row[0], row[1]) for row in rows)


async def drain_sends(sessions: async_sessionmaker[AsyncSession], tokens: SendTokens) -> None:
    """Wait outside owner locks. Only captured sends matter; later consent is independent."""
    if not tokens:
        return
    while True:
        async with sessions() as session, session.begin():
            criterion = tuple_(RewriteSendFenceRow.job_id, RewriteSendFenceRow.lease_token).in_(
                tokens
            )
            await session.execute(
                delete(RewriteSendFenceRow).where(
                    criterion, RewriteSendFenceRow.expires_at <= datetime.now(UTC)
                )
            )
            active = await session.scalar(
                select(RewriteSendFenceRow.job_id).where(criterion).limit(1)
            )
        if active is None:
            return
        await asyncio.sleep(0.05)
