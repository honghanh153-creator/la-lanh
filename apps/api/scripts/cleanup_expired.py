import argparse
import asyncio
from datetime import UTC, datetime
from time import monotonic

from app.config import get_settings
from app.db.session import Database
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
        return await _drain(PostgresHistoryRepository(database.sessions, envelope), now, batch_size)
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
