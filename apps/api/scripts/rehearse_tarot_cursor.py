"""Release rehearsal for the Tarot variant cursor (US-20 AC15, migration 20261018_0037).

Run inside ``infra/hetzner/rehearse-migration.sh`` against the disposable restored database, as the
least-privileged backend role, after ``alembic upgrade head``. It never touches production and needs
no production key: the guest, session keys and variety key are synthetic and created here.

Checks (runbook "Tarot B2 (US-20)"):

1. the connection role is not a superuser (PostgreSQL only);
2. ``tarot_variant_cursors`` has RLS enabled and no browser-role privileges (PostgreSQL only);
3. two concurrent session starts of one guest get distinct positions through the real upsert,
   and the variant records the two sessions actually stored (decrypted here, never printed) are
   the ones for positions 0 and 1 and differ on every axis;
4. deleting a reading keeps the cursor; retention cleanup, drained in bounded batches until the
   synthetic sessions are gone (a restored copy may hold many older expired sessions), keeps it;
   deleting the guest removes it.

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
from app.domains.tarot.tables import TarotSessionRow, TarotVariantCursorRow
from app.domains.tarot.variants import TarotVariants, choose_variants
from app.infrastructure.crypto import AesGcmEnvelopeCipher, SecretHasher, StaticDataKeyProvider

QUESTION = "Mình cần nói rõ điều gì trước khi nhận thêm việc?"
CLEANUP_BATCH = 1000
MAX_CLEANUP_BATCHES = 10_000  # 10 million expired sessions; a real copy is far smaller


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


async def _stored(db: Database, service: TarotSessionService, session_id: UUID) -> TarotVariants:
    async with db.sessions() as session:
        row = await session.get(TarotSessionRow, session_id)
        if row is None:
            raise RehearsalFailed("synthetic-session-missing")
        return TarotVariants.model_validate(service._decrypt(row)["variants"])


async def _present(db: Database, session_ids: set[UUID]) -> bool:
    async with db.sessions() as session:
        found = await session.scalar(
            select(TarotSessionRow.id).where(TarotSessionRow.id.in_(session_ids)).limit(1)
        )
        return found is not None


def _differ_on_every_axis(left: TarotVariants, right: TarotVariants) -> bool:
    return (
        left.lead != right.lead
        and left.headline != right.headline
        and all(left.frame(key) != right.frame(key) for key in left.frames)
    )


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
    variety_key = secrets.token_bytes(32)
    service = TarotSessionService(
        db.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(secrets.token_bytes(32))),
        SecretHasher(secrets.token_bytes(32)),
        variety_key=variety_key,
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
        first, second = await asyncio.gather(start("a"), start("b"))
        _require(await _cursor(db, guest) == 2, "concurrent-starts-did-not-both-allocate")
        stored = [await _stored(db, service, session_id) for session_id in (first, second)]
        keys = tuple(stored[0].frames)
        expected = [
            choose_variants(variety_key, guest, position, keys).model_dump(mode="json")
            for position in (0, 1)
        ]
        actual = [variants.model_dump(mode="json") for variants in stored]
        _require(
            sorted(map(str, actual)) == sorted(map(str, expected)),
            "concurrent-sessions-did-not-store-positions-0-and-1",
        )
        _require(_differ_on_every_axis(*stored), "concurrent-sessions-share-variants")
        await service.delete(guest, first)
        third = await start("c")
        _require(await _cursor(db, guest) == 3, "deletion-rewound-the-cursor")
        _require(
            (await _stored(db, service, third)).model_dump(mode="json")
            == choose_variants(variety_key, guest, 2, keys).model_dump(mode="json"),
            "session-after-deletion-did-not-store-position-2",
        )
        later = now + TarotSessionService.RETENTION_WINDOW + timedelta(days=1)
        synthetic = {second, third}
        for _ in range(MAX_CLEANUP_BATCHES):
            removed = await service.cleanup(batch_size=CLEANUP_BATCH, now=later)
            if not await _present(db, synthetic):
                break
            _require(removed > 0, "cleanup-did-not-reach-the-synthetic-sessions")
        else:
            raise RehearsalFailed("cleanup-did-not-finish")
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
