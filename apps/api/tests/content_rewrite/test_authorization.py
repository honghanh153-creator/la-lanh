from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.db.session import Database
from app.domains.content_rewrite.authorization import (
    DatabaseRewriteAuthorization,
    RewriteConsentScope,
    consent_definition,
    content_rewrite_receipt_id,
)
from app.domains.content_rewrite.models import ArtifactOwnerKey
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from tests.content_rewrite.test_repository import _request


async def test_only_twenty_active_consented_sessions_are_authorized(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'pilot.db'}")
    await database.initialize()
    now = datetime.now(UTC)
    definition = consent_definition(RewriteConsentScope.PERSONAL)
    ids = [UUID(int=index) for index in range(1, 22)]
    try:
        async with database.sessions() as session, session.begin():
            for index, guest_id in enumerate(ids):
                session.add(
                    GuestSessionRow(
                        id=guest_id,
                        token_hash=guest_id.bytes * 2,
                        csrf_hash=b"c" * 32,
                        state="active",
                        onboarding_status="birth_pending",
                        created_at=now,
                        last_active_at=now,
                        expires_at=now + timedelta(days=30),
                    )
                )
                await session.flush()
                session.add(
                    ConsentRow(
                        guest_id=guest_id,
                        version=definition.version,
                        purpose=definition.purpose,
                        accepted_at=now + timedelta(microseconds=index),
                    )
                )
        authorization = DatabaseRewriteAuthorization(database.sessions, pilot_user_limit=20)
        assert await authorization.pilot_eligible(ids[0])
        assert await authorization.pilot_eligible(ids[19])
        assert not await authorization.pilot_eligible(ids[20])
        request = _request(owner_key=f"daily|{ids[20]}|date|tradition|context").model_copy(
            update={"authorization_receipt_id": content_rewrite_receipt_id(ids[20])}
        )
        assert not await authorization.is_authorized(request)
        async with database.sessions() as session, session.begin():
            consent = await session.scalar(select(ConsentRow).where(ConsentRow.guest_id == ids[0]))
            assert consent is not None
            consent.revoked_at = now
        assert not await authorization.authorized_guest(ids[0])
        assert await authorization.pilot_eligible(ids[20])
        assert await authorization.is_authorized(request)
        async with database.sessions() as session, session.begin():
            guest = await session.get(GuestSessionRow, ids[20])
            assert guest is not None
            guest.created_at = now - timedelta(days=31)
            guest.expires_at = now - timedelta(days=1)
        unlimited = DatabaseRewriteAuthorization(database.sessions)
        assert not await unlimited.authorized_guest(ids[20])
        assert not await unlimited.is_authorized(request)
        unknown = _request().model_copy(
            update={
                "key": _request().key.model_copy(
                    update={
                        "owner": ArtifactOwnerKey(namespace="readings", key="invalid-owner"),
                    }
                ),
            }
        )
        assert not await unlimited.is_authorized(unknown)
    finally:
        await database.dispose()
