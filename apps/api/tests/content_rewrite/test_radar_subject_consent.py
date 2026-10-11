from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.session import Database
from app.domains.content_rewrite.authorization import (
    DatabaseRewriteAuthorization,
    RewriteConsentScope,
    consent_definition,
)
from app.domains.content_rewrite.models import RewriteJobRecord
from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
from app.domains.content_rewrite.tables import ContentRewriteJobRow
from app.domains.guest.postgres import PostgresGuestRepository
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.identity.tables import PrincipalRow
from app.domains.radar.rewrite import compile_radar_rewrite_request
from app.domains.radar.tables import RadarRequestRow
from app.domains.tarot.models import TarotSessionView
from app.infrastructure.crypto import EnvelopeCipher
from tests.content_rewrite.test_execution_fences import fenced as fenced
from tests.content_rewrite.test_radar_rewrite import _projection


@pytest.mark.parametrize(
    "other_consents,mode",
    [(False, "consented_invite"), (True, "private_check"), (True, "consented_invite")],
)
@pytest.mark.parametrize("withdrawal", ["legacy", "repository", "reconsent"])
async def test_radar_requires_both_subjects_before_enqueue_and_execution(
    fenced: tuple[
        Database,
        PostgresContentRewriteRepository,
        EnvelopeCipher,
        UUID,
        TarotSessionView,
        RewriteJobRecord,
    ],
    other_consents: bool,
    mode: str,
    withdrawal: str,
) -> None:
    db, repository, _, owner_id, _, _ = fenced
    now = datetime.now(UTC)
    other_id, principal_id, radar_id = uuid4(), uuid4(), uuid4()
    definition = consent_definition(RewriteConsentScope.RADAR)
    async with db.sessions() as session, session.begin():
        session.add(
            GuestSessionRow(
                id=other_id,
                token_hash=other_id.bytes * 2,
                csrf_hash=b"x" * 32,
                state="active",
                onboarding_status="birth_pending",
                created_at=now,
                last_active_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
        await session.flush()
        session.add(PrincipalRow(id=principal_id, source_guest_id=owner_id, created_at=now))
        for guest_id in (owner_id, other_id) if other_consents else (owner_id,):
            session.add(
                ConsentRow(
                    guest_id=guest_id,
                    purpose=definition.purpose,
                    version=definition.version,
                    accepted_at=now,
                )
            )
        await session.flush()
        session.add(
            RadarRequestRow(
                id=radar_id,
                principal_id=principal_id,
                owner_guest_id=owner_id,
                recipient_guest_id=other_id if mode == "consented_invite" else None,
                recipient_label_ciphertext="encrypted-test-label",
                context="crush",
                mode=mode,
                status="completed",
                created_at=now,
                expires_at=now + timedelta(days=1),
            )
        )
    request = compile_radar_rewrite_request(
        owner_id,
        radar_id,
        "owner",
        _projection(),
        context="crush",
        model_version="gpt-6-luna",
        prompt_version="offline",
    )
    assert request is not None
    permitted = other_consents and mode == "consented_invite"
    authorization = DatabaseRewriteAuthorization(db.sessions)
    assert await authorization.is_authorized(request) is permitted
    record = RewriteJobRecord(
        id=uuid4(),
        request=request,
        deletion_epoch=uuid4(),
        created_at=now,
        updated_at=now,
        next_attempt_at=now,
    )
    if not permitted:
        with pytest.raises(PermissionError):
            await repository.enqueue(record)
        return
    await repository.enqueue(record)
    # The fixture also has a Tarot job. Lease it first, then the Radar request.
    assert await repository.lease(now=now, lease_for_seconds=120)
    lease = await repository.lease(now=now, lease_for_seconds=120)
    assert lease is not None and lease.id == record.id
    async with repository.execution_guard(lease) as allowed:
        assert allowed is True
    async with db.sessions() as session, session.begin():
        other_consent = await session.scalar(
            select(ConsentRow).where(
                ConsentRow.guest_id == other_id,
                ConsentRow.purpose == definition.purpose,
            )
        )
        assert other_consent is not None
        if withdrawal == "legacy":
            other_consent.revoked_at = datetime.now(UTC)
        elif withdrawal == "reconsent":
            other_consent.accepted_at = datetime.now(UTC)
    if withdrawal == "repository":
        await PostgresGuestRepository(db.sessions).revoke_consent(
            other_id, definition.purpose, datetime.now(UTC)
        )
        async with db.sessions() as session:
            assert await session.get(ContentRewriteJobRow, record.id) is None
            assert await session.get(RadarRequestRow, radar_id) is not None
    assert await authorization.is_authorized(request) is (withdrawal == "reconsent")
    async with repository.execution_guard(lease) as allowed:
        assert allowed is False
