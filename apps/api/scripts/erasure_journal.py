"""Deletion journal operations (audit P07, option A). Output never contains ids or content.

export                        JSON lines on stdout, for the host-side copy and before a restore
replay FILE [FILE ...]        apply to a restored database every exported erasure its
                              snapshot does not hold (the dump's journal rows are the checkpoint)
purge [--retention-days N]    drop entries older than the oldest restorable backup
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import get_settings
from app.db.session import Database
from app.domains.erasure_journal.journal import ErasureJournal
from app.domains.erasure_journal.replay import export_entries, purge_entries, replay
from app.domains.human_tarot import policy
from app.domains.human_tarot.service import HumanTarotService
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    database = Database(str(settings.database_url))
    await database.initialize()
    try:
        if args.command == "export":
            for line in await export_entries(database.sessions):
                print(line)
            return 0
        if args.command == "purge":
            days = args.retention_days or settings.erasure_journal_retention_days
            removed = await purge_entries(
                database.sessions, before=datetime.now(UTC) - timedelta(days=days)
            )
            print(f"Purged {removed} journal entr(y/ies) older than {days} days.", file=sys.stderr)
            return 0
        journal_hasher = SecretHasher(decode_key(settings.guest_hash_key.get_secret_value()))
        journal = ErasureJournal(journal_hasher)
        envelope = AesGcmEnvelopeCipher(
            StaticDataKeyProvider(
                decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
            )
        )
        report = await replay(database.sessions, journal, envelope, args.lines)
        for line in report.lines():
            print(line)
        # US-24: a restored day tally may be lower than what was really accepted; stop today's
        # human Tarot intake instead of trusting it (the Sheet bridge clears unknown rows).
        human_tarot = HumanTarotService(database.sessions, envelope, journal_hasher)
        today = policy.local_day(human_tarot.now())
        await human_tarot.close_intake(today)
        print(f"human_tarot_intake_closed day={today.isoformat()}")
        print("Next: run the guest and expired cleanup jobs before serving.")
        return 0
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Deletion journal operations (audit P07).")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("export")
    again = commands.add_parser("replay")
    again.add_argument("files", nargs="+")
    purge = commands.add_parser("purge")
    purge.add_argument("--retention-days", type=int)
    args = parser.parse_args()
    if args.command == "replay":
        # Read before the event loop starts: the files are small exported digest lists.
        args.lines = [line for path in args.files for line in Path(path).read_text().splitlines()]
    if args.command == "purge" and args.retention_days is not None and args.retention_days < 1:
        parser.error("--retention-days must be at least 1")
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
