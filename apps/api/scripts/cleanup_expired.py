import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from time import monotonic

from app.config import get_settings
from app.db.session import Database
from app.domains.erasure_journal.replay import purge_entries
from app.domains.history.postgres import PostgresHistoryRepository
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    StaticDataKeyProvider,
    decode_key,
)


async def _drain(repository: PostgresHistoryRepository, now: datetime, batch_size: int) -> int:
    deadline = monotonic() + 300
    total = 0
    for pass_number in range(1, 101):
        removed = await repository.purge_expired(now, batch_size)
        total += removed
        remaining = await repository.remaining(now)
        print(f"History pass {pass_number}: purged={removed} remaining={remaining}", flush=True)
        if remaining == 0:
            return total
        if removed == 0 or monotonic() >= deadline:
            raise RuntimeError(f"History cleanup incomplete: remaining={remaining}; retry required")
    raise RuntimeError(f"History cleanup pass limit reached: remaining={remaining}; retry required")


async def _cleanup(batch_size: int) -> int:
    settings = get_settings()
    database = Database(str(settings.database_url))
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(
        StaticDataKeyProvider(
            decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
        )
    )
    now = datetime.now(UTC)
    try:
        removed = await _drain(
            PostgresHistoryRepository(database.sessions, envelope), now, batch_size
        )
        # Deletion-journal retention also runs here, so it holds even before the hourly host
        # copy is installed (audit P07, option A).
        journal = await purge_entries(
            database.sessions,
            before=now - timedelta(days=settings.erasure_journal_retention_days),
        )
        print(f"Deletion journal: purged={journal}", flush=True)
        return removed
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drain expired history in bounded owner-locked batches."
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 1000:
        parser.error("--batch-size must be between 1 and 1000")
    total = asyncio.run(_cleanup(args.batch_size))
    print(f"Purged {total} history root(s) and their dependent rows; remaining=0.")


if __name__ == "__main__":
    main()
