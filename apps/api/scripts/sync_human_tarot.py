"""One pass of the human Tarot Sheet bridge (US-24 U5), run every minute by the host timer.

    python -m scripts.sync_human_tarot            # export, import, clear, retention
    python -m scripts.sync_human_tarot close-today # stop today's intake (restore runbook)

Refuses to touch Google unless ``LA_LANH_HUMAN_TAROT_SHEET_SYNC_ENABLED`` and the Sheet settings
are configured. Prints counts and closed error codes only.
"""

import argparse
import asyncio
import sys

from app.config import Settings, get_settings
from app.db.session import Database
from app.domains.daily import tables as daily_tables  # noqa: F401 - local SQLite create_all
from app.domains.human_tarot import policy
from app.domains.human_tarot.service import HumanTarotService
from app.domains.human_tarot.sheets import GoogleBudget, HumanTarotSheetBridge
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    SecretHasher,
    StaticDataKeyProvider,
    decode_key,
)
from app.infrastructure.google_sheets.client import GoogleSheetsClient, ServiceAccount


def _service(settings: Settings, database: Database) -> HumanTarotService:
    return HumanTarotService(
        database.sessions,
        AesGcmEnvelopeCipher(
            StaticDataKeyProvider(
                decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
            )
        ),
        SecretHasher(decode_key(settings.guest_hash_key.get_secret_value())),
        enabled=settings.human_tarot_enabled,
        intake_closes_at=settings.human_tarot_intake_closes_at,
    )


async def _run(command: str) -> int:
    settings = get_settings()
    database = Database(str(settings.database_url))
    await database.initialize()
    try:
        service = _service(settings, database)
        if command == "close-today":
            day = policy.local_day(service.now())
            await service.close_intake(day)
            print(f"human_tarot_intake_closed day={day.isoformat()}")
            return 0
        if not settings.human_tarot_sheet_sync_enabled:
            print("human_tarot_sync disabled")
            return 0
        sheet_id, credentials_file = settings.human_tarot_sheet()
        budget = GoogleBudget(database.sessions, service.now)
        gateway = GoogleSheetsClient(
            sheet_id, ServiceAccount.from_file(credentials_file), reserve=budget.reserve
        )
        report = await HumanTarotSheetBridge(
            database.sessions, service, gateway, budget=budget
        ).sync_once()
        print(report.line())
        return 1 if report.error is not None else 0
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Human Tarot Sheet bridge (US-24).")
    parser.add_argument("command", nargs="?", default="sync", choices=("sync", "close-today"))
    args = parser.parse_args()
    sys.exit(asyncio.run(_run(args.command)))


if __name__ == "__main__":
    main()
