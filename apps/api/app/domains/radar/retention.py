"""Hourly retention for the Hợp gu keepsakes (run by ``scripts.cleanup_expired``).

Reads already hide expired rows; this deletes them, so a kept "Hai bạn tuần này" pair (at most
90 days, owner AQ1/AR1 21.11.2026) and a card link (never longer than its result) do not linger
in the database after their time is up.
"""

from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.radar.tables import RadarShareCardRow, RadarWeeklyPairRow


async def purge_expired_keepsakes(
    sessions: async_sessionmaker[AsyncSession], *, now: datetime
) -> dict[str, int]:
    async with sessions() as session, session.begin():
        weekly = await session.execute(
            delete(RadarWeeklyPairRow).where(RadarWeeklyPairRow.expires_at <= now)
        )
        cards = await session.execute(
            delete(RadarShareCardRow).where(RadarShareCardRow.expires_at <= now)
        )
    return {
        "weekly_pairs": int(getattr(weekly, "rowcount", 0) or 0),
        "card_links": int(getattr(cards, "rowcount", 0) or 0),
    }
