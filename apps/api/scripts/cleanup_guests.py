import argparse
import asyncio
from datetime import UTC, datetime

from app.config import get_settings
from app.db.session import Database
from app.domains.guest.postgres import PostgresGuestRepository


async def _cleanup(batch_size: int) -> int:
    settings = get_settings()
    database = Database(str(settings.database_url))
    await database.initialize()
    try:
        repository = PostgresGuestRepository(database.sessions)
        return await repository.purge_expired(datetime.now(UTC), batch_size)
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge expired guest sessions and replay tokens.")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 1000:
        parser.error("--batch-size must be between 1 and 1000")
    purged = asyncio.run(_cleanup(args.batch_size))
    print(f"Purged {purged} expired guest session(s).")


if __name__ == "__main__":
    main()
