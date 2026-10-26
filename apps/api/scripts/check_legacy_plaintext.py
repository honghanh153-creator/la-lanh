"""Count rows still readable through a legacy plaintext column (audit 2026-10-22 P06).

    LA_LANH_DATABASE_URL=... uv run python -m scripts.check_legacy_plaintext [--fail-on-legacy]

Aggregate only: one count per check, never a value, an identifier or a sample row. It opens a
read-only transaction and changes nothing. The operator runs it with protected credentials; this
task only prepares it (no production access here). A zero proves only that these known columns are
empty at that moment; backups and provider copies follow their own lifecycles.

Each check is a column that a compatibility reader still accepts (``birth``, ``daily``, ``saved``,
``share`` and La Chung repositories) or that new writes must leave empty. The key-aware backfill or
purge plan for non-zero results is ``docs/operations/legacy-plaintext-backfill-plan.md``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Text, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.sql.elements import ColumnElement

from app.db.session import verified_engine_options
from app.domains.birth.tables import BirthProfileRow, ChartSnapshotRow
from app.domains.daily.tables import DailyNoteRow
from app.domains.la_chung.tables import LaChungRequestRow
from app.domains.saved.tables import SavedNoteRow
from app.domains.share.tables import ShareArtifactRow


def _filled_json(column: Any) -> ColumnElement[bool]:
    filled: ColumnElement[bool] = (
        column.is_not(None) & (cast(column, Text) != "{}") & (cast(column, Text) != "null")
    )
    return filled


def _filled_text(*columns: Any) -> ColumnElement[bool]:
    return or_(*(column.is_not(None) & (column != "") for column in columns))


@dataclass(frozen=True)
class Check:
    key: str
    table: type
    criteria: ColumnElement[bool]
    meaning: str


CHECKS: tuple[Check, ...] = (
    Check(
        "chart_snapshots.result_payload",
        ChartSnapshotRow,
        # New writes pass None, which the JSON type stores as JSON null, not SQL NULL.
        _filled_json(ChartSnapshotRow.result_payload),
        "chart result readable without the envelope (birth/postgres.py _result_payload)",
    ),
    Check(
        "birth_profiles.place_plaintext",
        BirthProfileRow,
        _filled_text(BirthProfileRow.place_display_name, BirthProfileRow.timezone_id),
        "birthplace name or time zone in plaintext columns new writes set to NULL",
    ),
    Check(
        "daily_notes.unencrypted",
        DailyNoteRow,
        DailyNoteRow.content_ciphertext.is_(None),
        "Daily prose read from title/body columns (daily/postgres.py _content)",
    ),
    Check(
        "daily_notes.plaintext_beside_ciphertext",
        DailyNoteRow,
        DailyNoteRow.content_ciphertext.is_not(None)
        & _filled_text(
            DailyNoteRow.title,
            DailyNoteRow.body,
            DailyNoteRow.full_body,
            DailyNoteRow.context_label,
        ),
        "encrypted Daily row whose legacy prose columns are not blank",
    ),
    Check(
        "saved_notes.unencrypted",
        SavedNoteRow,
        SavedNoteRow.snapshot_ciphertext.is_(None),
        "saved snapshot read from JSON columns (saved/postgres.py _snapshot_payload)",
    ),
    Check(
        "saved_notes.plaintext_beside_ciphertext",
        SavedNoteRow,
        SavedNoteRow.snapshot_ciphertext.is_not(None)
        & or_(
            _filled_json(SavedNoteRow.note_snapshot),
            _filled_json(SavedNoteRow.reading_snapshot),
        ),
        "encrypted saved row whose legacy JSON is not empty",
    ),
    Check(
        "share_artifacts.unencrypted",
        ShareArtifactRow,
        ShareArtifactRow.safe_snapshot_ciphertext.is_(None),
        "share snapshot read from JSON (share/postgres.py _snapshot_payload)",
    ),
    Check(
        "share_artifacts.plaintext_beside_ciphertext",
        ShareArtifactRow,
        ShareArtifactRow.safe_snapshot_ciphertext.is_not(None)
        & _filled_json(ShareArtifactRow.safe_snapshot),
        "encrypted share row whose legacy JSON is not empty",
    ),
    Check(
        "la_chung_requests.recipient_label",
        LaChungRequestRow,
        _filled_text(LaChungRequestRow.recipient_label),
        "La Chung recipient label in the pre-encryption column",
    ),
)


async def count_legacy(connection: AsyncConnection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for check in CHECKS:
        statement = select(func.count()).select_from(check.table).where(check.criteria)
        counts[check.key] = int(await connection.scalar(statement) or 0)
    return counts


async def run(url: str) -> dict[str, int]:
    engine = create_async_engine(**verified_engine_options(url), pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                await connection.execute(text("SET TRANSACTION READ ONLY"))
            counts = await count_legacy(connection)
            await connection.rollback()
            return counts
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fail-on-legacy", action="store_true")
    args = parser.parse_args(argv)
    try:
        counts = asyncio.run(run(os.environ["LA_LANH_DATABASE_URL"]))
    except Exception as error:  # never print the URL or a driver message with a value
        print(f"legacy-plaintext-check-failed:{type(error).__name__}")
        return 1
    print(json.dumps({"legacy_plaintext_counts": counts}, sort_keys=True))
    return 1 if args.fail_on_legacy and any(counts.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
