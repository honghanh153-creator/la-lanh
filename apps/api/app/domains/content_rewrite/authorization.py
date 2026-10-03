from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.service import RewriteAuthorizationChecker
from app.domains.guest.tables import ConsentRow

CONTENT_REWRITE_CONSENT_VERSION = "external-content-rewrite-v1"
CONTENT_REWRITE_CONSENT_PURPOSE = "external_content_rewrite"
RADAR_REWRITE_CONSENT_VERSION = "external-radar-rewrite-v1"
RADAR_REWRITE_CONSENT_PURPOSE = "external_radar_rewrite"
MATCHING_REWRITE_CONSENT_VERSION = "external-matching-rewrite-v1"
MATCHING_REWRITE_CONSENT_PURPOSE = "external_matching_rewrite"


class RewriteConsentScope(StrEnum):
    PERSONAL = "personal"
    RADAR = "radar"
    MATCHING = "matching"


@dataclass(frozen=True, slots=True)
class RewriteConsentDefinition:
    version: str
    purpose: str


_CONSENT_BY_SCOPE = {
    RewriteConsentScope.PERSONAL: RewriteConsentDefinition(
        CONTENT_REWRITE_CONSENT_VERSION,
        CONTENT_REWRITE_CONSENT_PURPOSE,
    ),
    RewriteConsentScope.RADAR: RewriteConsentDefinition(
        RADAR_REWRITE_CONSENT_VERSION,
        RADAR_REWRITE_CONSENT_PURPOSE,
    ),
    RewriteConsentScope.MATCHING: RewriteConsentDefinition(
        MATCHING_REWRITE_CONSENT_VERSION,
        MATCHING_REWRITE_CONSENT_PURPOSE,
    ),
}


def consent_definition(scope: RewriteConsentScope) -> RewriteConsentDefinition:
    return _CONSENT_BY_SCOPE[scope]


def consent_scope_for_surface(surface: RewriteSurface) -> RewriteConsentScope:
    if surface is RewriteSurface.RADAR:
        return RewriteConsentScope.RADAR
    if surface is RewriteSurface.MATCHING:
        return RewriteConsentScope.MATCHING
    return RewriteConsentScope.PERSONAL


def content_rewrite_receipt_id(
    guest_id: UUID,
    *,
    scope: RewriteConsentScope = RewriteConsentScope.PERSONAL,
) -> str:
    definition = consent_definition(scope)
    return sha256(
        f"{definition.version}\x00{definition.purpose}\x00{guest_id}".encode()
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
    if owner.namespace == "radar" and len(parts) == 4 and parts[0] == "radar":
        return UUID(parts[1])
    if owner.namespace == "matching" and len(parts) == 4 and parts[0] == "matching":
        return UUID(parts[1])
    raise ValueError("rewrite owner does not expose an authorized guest")


class DatabaseRewriteAuthorization(RewriteAuthorizationChecker):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def authorized_guest(
        self,
        guest_id: UUID,
        *,
        scope: RewriteConsentScope = RewriteConsentScope.PERSONAL,
    ) -> bool:
        definition = consent_definition(scope)
        async with self._sessions() as session:
            consent = await session.scalar(
                select(ConsentRow).where(
                    ConsentRow.guest_id == guest_id,
                    ConsentRow.version == definition.version,
                    ConsentRow.purpose == definition.purpose,
                    ConsentRow.revoked_at.is_(None),
                )
            )
            return consent is not None

    async def is_authorized(self, request: RewriteRequestEnvelope) -> bool:
        try:
            guest_id = guest_id_from_rewrite_owner(request.key.owner)
        except ValueError:
            return False
        scope = consent_scope_for_surface(request.key.surface)
        if request.authorization_receipt_id != content_rewrite_receipt_id(
            guest_id,
            scope=scope,
        ):
            return False
        return await self.authorized_guest(guest_id, scope=scope)
