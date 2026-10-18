"""Release rehearsal for the Tarot variant cursor (US-20 AC15, migration 20261018_0037).

Run inside ``infra/hetzner/rehearse-migration.sh`` against the disposable restored database, as the
least-privileged backend role, after ``alembic upgrade head``. It never touches production and needs
no production key: the guest, session keys and variety key are synthetic and created here.

Checks (runbook "Tarot B2 (US-20)"):

1. the connection role is not a superuser (PostgreSQL only);
2. ``tarot_variant_cursors`` has RLS enabled and no browser-role privileges (PostgreSQL only);
3. two concurrent session starts of one guest get distinct positions through the real upsert;
4. deleting a reading and retention cleanup keep the cursor; deleting the guest removes it.

Cleanup runs with a far-future clock, so it also purges the restored copy's other Tarot sessions;
the copy is disposable and destroyed by the rehearsal script.

Prints ``tarot-cursor-rehearsal-ok`` and exits 0, or prints a failure code and exits 1.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, select, text

from app.db.session import Database
from app.domains.guest.tables import GuestSessionRow
from app.domains.tarot.models import TarotContext, TarotOrigin, TarotSpread, TarotVoice
from app.domains.tarot.service import TarotSessionService
from app.domains.tarot.tables import TarotVariantCursorRow
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

QUESTION = "Mình cần nói rõ điều gì trước khi nhận thêm việc?"


class RehearsalFailed(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RehearsalFailed(code)


async def check_postgres_role_and_isolation(db: Database) -> None:
    async with db.engine.connect() as connection:
        superuser = await connection.scalar(
            text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        )
        _require(superuser is False, "connection-role-is-superuser")
        rls = await connection.scalar(
            text("SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:name)"),
            {"name": "public.tarot_variant_cursors"},
        )
        _require(rls is True, "cursor-table-without-rls")
        exposed = await connection.scalar(
            text("""
            SELECT count(*) FROM pg_roles r
            WHERE r.rolname IN ('anon', 'authenticated')
            AND has_table_privilege(r.oid, 'public.tarot_variant_cursors',
                'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
            """)
        )
        _require(exposed == 0, "cursor-table-reachable-by-browser-roles")
        public = await connection.scalar(
            text("""
            SELECT has_table_privilege('public', 'public.tarot_variant_cursors', 'SELECT')
            """)
        )
        _require(public is False, "cursor-table-readable-by-public")


async def _cursor(db: Database, guest: UUID) -> int | None:
    async with db.sessions() as session:
        row = await session.get(TarotVariantCursorRow, guest)
        return None if row is None else row.next_position


async def exercise_cursor(db: Database) -> None:
    """Synthetic guest, real service and upsert; removes everything it created."""

    now = datetime.now(UTC)
    guest = uuid4()
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=guest,
                token_hash=secrets.token_bytes(32),
                csrf_hash=secrets.token_bytes(32),
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
    service = TarotSessionService(
        db.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(secrets.token_bytes(32))),
        SecretHasher(secrets.token_bytes(32)),
        variety_key=secrets.token_bytes(32),
    )

    async def start(tag: str) -> UUID:
        view = await service.start(
            guest_id=guest,
            context=TarotContext.WORK,
            question=QUESTION,
            spread=TarotSpread.THREE_CARD,
            voice=TarotVoice.PLAYFUL_GROUNDED,
            origin=TarotOrigin.DIRECT,
            idempotency_key=f"tarot-rehearsal-{tag}-{secrets.token_hex(8)}",
        )
        return view.id

    try:
        first, _second = await asyncio.gather(start("a"), start("b"))
        _require(await _cursor(db, guest) == 2, "concurrent-starts-share-a-position")
        await service.delete(guest, first)
        await start("c")
        _require(await _cursor(db, guest) == 3, "deletion-rewound-the-cursor")
        later = now + TarotSessionService.RETENTION_WINDOW + timedelta(days=1)
        await service.cleanup(now=later)
        _require(await _cursor(db, guest) == 3, "cleanup-rewound-the-cursor")
    finally:
        async with db.sessions() as session, session.begin():
            await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest))
    async with db.sessions() as session:
        remaining = await session.scalar(
            select(TarotVariantCursorRow.guest_id).where(TarotVariantCursorRow.guest_id == guest)
        )
    _require(remaining is None, "cursor-survived-guest-deletion")


async def rehearse(database_url: str) -> None:
    db = Database(database_url)
    try:
        if db.engine.dialect.name == "postgresql":
            await check_postgres_role_and_isolation(db)
        await exercise_cursor(db)
    finally:
        await db.dispose()


def main() -> int:
    try:
        asyncio.run(rehearse(os.environ["LA_LANH_DATABASE_URL"]))
    except RehearsalFailed as failure:
        print(f"tarot-cursor-rehearsal-failed:{failure}")
        return 1
    except Exception as error:  # never print connection details
        print(f"tarot-cursor-rehearsal-failed:{type(error).__name__}")
        return 1
    print("tarot-cursor-rehearsal-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
