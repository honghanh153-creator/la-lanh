import argparse
import asyncio
from datetime import UTC, datetime

from app.config import get_settings
from app.db.session import Database
from app.domains.experiments.postgres import PostgresExperimentRepository
from app.domains.resonance.postgres import PostgresResonanceRepository
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider, decode_key


async def _cleanup(batch_size: int) -> tuple[int, int]:
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
        experiments = await PostgresExperimentRepository(database.sessions, envelope).purge_expired(
            now=now, batch_size=batch_size
        )
        resonance = await PostgresResonanceRepository(database.sessions, envelope).purge_expired(
            now=now, batch_size=batch_size
        )
        return experiments, resonance
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Physically purge expired bounded feedback.")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 1000:
        parser.error("--batch-size must be between 1 and 1000")
    experiments, resonance = asyncio.run(_cleanup(args.batch_size))
    print(f"Purged {experiments} experiment(s) and {resonance} resonance row(s).")


if __name__ == "__main__":
    main()
