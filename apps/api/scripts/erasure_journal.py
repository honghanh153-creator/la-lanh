"""Deletion journal operations (audit P07, option A). Output never contains ids or content.

export [--since ISO]          JSON lines on stdout, for the host-side copy and before a restore
import FILE [FILE ...]        add exported entries to a restored database
replay --since ISO            re-apply erasures newer than the restored dump's time
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
from app.domains.erasure_journal.replay import (
    export_entries,
    import_entries,
    purge_entries,
    replay,
)
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)


def _when(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise argparse.ArgumentTypeError("time must carry a UTC offset")
    return moment


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    database = Database(str(settings.database_url))
    await database.initialize()
    try:
        if args.command == "export":
            for line in await export_entries(database.sessions, since=args.since):
                print(line)
            return 0
        if args.command == "import":
            lines = args.lines
            print(f"Imported {await import_entries(database.sessions, lines)} journal entr(y/ies).")
            return 0
        if args.command == "purge":
            days = args.retention_days or settings.erasure_journal_retention_days
            removed = await purge_entries(
                database.sessions, before=datetime.now(UTC) - timedelta(days=days)
            )
            print(f"Purged {removed} journal entr(y/ies) older than {days} days.", file=sys.stderr)
            return 0
        journal = ErasureJournal(
            SecretHasher(decode_key(settings.guest_hash_key.get_secret_value()))
        )
        envelope = AesGcmEnvelopeCipher(
            StaticDataKeyProvider(
                decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
            )
        )
        report = await replay(database.sessions, journal, envelope, since=args.since)
        for line in report.lines():
            print(line)
        print("Next: run the guest and expired cleanup jobs before serving.")
        return 0
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Deletion journal operations (audit P07).")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--since", type=_when)
    load = commands.add_parser("import")
    load.add_argument("files", nargs="+")
    again = commands.add_parser("replay")
    again.add_argument("--since", type=_when, required=True)
    purge = commands.add_parser("purge")
    purge.add_argument("--retention-days", type=int)
    args = parser.parse_args()
    if args.command == "import":
        # Read before the event loop starts: the files are small exported digest lists.
        args.lines = [line for path in args.files for line in Path(path).read_text().splitlines()]
    if args.command == "purge" and args.retention_days is not None and args.retention_days < 1:
        parser.error("--retention-days must be at least 1")
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
