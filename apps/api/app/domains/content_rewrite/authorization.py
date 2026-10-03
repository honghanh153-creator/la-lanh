from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.models import ArtifactOwnerKey, RewriteRequestEnvelope
from app.domains.content_rewrite.service import RewriteAuthorizationChecker
from app.domains.guest.tables import ConsentRow

CONTENT_REWRITE_CONSENT_VERSION = "external-content-rewrite-v1"
CONTENT_REWRITE_CONSENT_PURPOSE = "external_content_rewrite"


def content_rewrite_receipt_id(guest_id: UUID) -> str:
    return sha256(
        f"{CONTENT_REWRITE_CONSENT_VERSION}\x00{CONTENT_REWRITE_CONSENT_PURPOSE}\x00{guest_id}".encode()
    ).hexdigest()


def guest_id_from_rewrite_owner(owner: ArtifactOwnerKey) -> UUID:
    parts = owner.key.split("|")
    if owner.namespace == "readings":
        if len(parts) == 5 and parts[0] == "daily":
            return UUID(parts[1])
        if len(parts) == 6 and parts[0] == "reading":
            return UUID(parts[2])
    if owner.namespace == "tarot" and len(parts) == 3 and parts[0] == "tarot":
        return UUID(parts[1])
    raise ValueError("rewrite owner does not expose an authorized guest")


class DatabaseRewriteAuthorization(RewriteAuthorizationChecker):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def authorized_guest(self, guest_id: UUID) -> bool:
        async with self._sessions() as session:
            consent = await session.scalar(
                select(ConsentRow).where(
                    ConsentRow.guest_id == guest_id,
                    ConsentRow.version == CONTENT_REWRITE_CONSENT_VERSION,
                    ConsentRow.purpose == CONTENT_REWRITE_CONSENT_PURPOSE,
                    ConsentRow.revoked_at.is_(None),
                )
            )
            return consent is not None

    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool:
        try:
            guest_id = guest_id_from_rewrite_owner(request.key.owner)
        except ValueError:
            return False
        if request.authorization_receipt_id != content_rewrite_receipt_id(guest_id):
            return False
        return await self.authorized_guest(guest_id)
