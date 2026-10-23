from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.content_rewrite.models import (
    ArtifactOwnerKey,
    RewriteRequestEnvelope,
    RewriteSurface,
)
from app.domains.content_rewrite.service import RewriteAuthorizationChecker
from app.domains.guest.models import GuestState
from app.domains.guest.tables import ConsentRow, GuestSessionRow
from app.domains.radar.tables import RadarRequestRow

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
    if owner.namespace == "share" and len(parts) == 4 and parts[0] in {"share", "recap"}:
        return UUID(parts[1])
    raise ValueError("rewrite owner does not expose an authorized guest")


async def rewrite_subjects(
    session: AsyncSession, request: RewriteRequestEnvelope, guest_id: UUID
) -> tuple[UUID, ...] | None:
    if request.key.surface is not RewriteSurface.RADAR:
        return None if request.key.owner.namespace == "radar" else (guest_id,)
    parts = request.key.owner.key.split("|")
    if request.key.owner.namespace != "radar" or len(parts) != 4:
        return None
    try:
        radar_id = UUID(parts[2])
    except ValueError:
        return None
    radar = await session.scalar(
        select(RadarRequestRow)
        .where(RadarRequestRow.id == radar_id)
        .execution_options(populate_existing=True)
    )
    if (
        radar is None
        or radar.mode != "consented_invite"
        or radar.status != "completed"
        or radar.withdrawn_at is not None
        or radar.revoked_at is not None
        or radar.expires_at <= datetime.now(UTC)
        or radar.recipient_guest_id is None
        or radar.recipient_guest_id == radar.owner_guest_id
        or parts[3] not in {"owner", "recipient"}
        or guest_id != (radar.owner_guest_id if parts[3] == "owner" else radar.recipient_guest_id)
    ):
        return None
    return tuple(sorted((radar.owner_guest_id, radar.recipient_guest_id), key=lambda id: id.int))


@dataclass(frozen=True, slots=True)
class LockedRewriteAuthority:
    accepted_at: datetime
    expires_at: datetime


async def lock_rewrite_authority(
    session: AsyncSession, request: RewriteRequestEnvelope, guest_id: UUID
) -> LockedRewriteAuthority | None:
    """Lock all data subjects before consent, parent and job locks."""
    subjects = await rewrite_subjects(session, request, guest_id)
    if subjects is None:
        return None
    scope = consent_scope_for_surface(request.key.surface)
    if request.authorization_receipt_id != content_rewrite_receipt_id(guest_id, scope=scope):
        return None
    guests = []
    for subject_id in subjects:
        guests.append(
            await session.scalar(
                select(GuestSessionRow).where(GuestSessionRow.id == subject_id).with_for_update()
            )
        )
    definition = consent_definition(scope)
    accepted = []
    for subject_id in subjects:
        consent = await session.scalar(
            select(ConsentRow)
            .where(
                ConsentRow.guest_id == subject_id,
                ConsentRow.purpose == definition.purpose,
                ConsentRow.version == definition.version,
                ConsentRow.revoked_at.is_(None),
            )
            .with_for_update()
        )
        if consent is None:
            return None
        accepted.append(consent.accepted_at)
    now = datetime.now(UTC)
    if any(
        guest is None or guest.state != GuestState.ACTIVE.value or guest.expires_at <= now
        for guest in guests
    ):
        return None
    if await rewrite_subjects(session, request, guest_id) != subjects:
        return None
    return LockedRewriteAuthority(
        accepted_at=max(accepted),
        expires_at=min(guest.expires_at for guest in guests if guest is not None),
    )


class DatabaseRewriteAuthorization(RewriteAuthorizationChecker):
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], *, pilot_user_limit: int = 0
    ) -> None:
        self._sessions = sessions
        self._pilot_user_limit = pilot_user_limit

    async def pilot_eligible(self, guest_id: UUID) -> bool:
        """Whether the guest holds one of the first ``pilot_user_limit`` participant slots.

        A slot belongs to a person, whatever the surface: every active external-rewrite consent
        (personal, Radar or matching) counts, ordered by each guest's earliest acceptance.
        Counting personal consents only let Radar- or matching-only guests through without ever
        occupying a slot (audit P03 RC-05).
        """

        if not self._pilot_user_limit:
            return True
        definitions = [consent_definition(scope) for scope in RewriteConsentScope]
        first_accepted = func.min(ConsentRow.accepted_at)
        async with self._sessions() as session:
            participants = tuple(
                await session.scalars(
                    select(ConsentRow.guest_id)
                    .join(GuestSessionRow, GuestSessionRow.id == ConsentRow.guest_id)
                    .where(
                        or_(
                            *(
                                (ConsentRow.version == item.version)
                                & (ConsentRow.purpose == item.purpose)
                                for item in definitions
                            )
                        ),
                        ConsentRow.revoked_at.is_(None),
                        GuestSessionRow.expires_at > datetime.now(UTC),
                        GuestSessionRow.state == GuestState.ACTIVE.value,
                    )
                    .group_by(ConsentRow.guest_id)
                    .order_by(first_accepted, ConsentRow.guest_id)
                    .limit(self._pilot_user_limit)
                )
            )
        return guest_id in participants or len(participants) < self._pilot_user_limit

    async def authorized_guest(
        self,
        guest_id: UUID,
        *,
        scope: RewriteConsentScope = RewriteConsentScope.PERSONAL,
    ) -> bool:
        definition = consent_definition(scope)
        async with self._sessions() as session:
            consent = await session.scalar(
                select(ConsentRow)
                .where(
                    ConsentRow.guest_id == guest_id,
                    ConsentRow.version == definition.version,
                    ConsentRow.purpose == definition.purpose,
                    ConsentRow.revoked_at.is_(None),
                )
                .join(GuestSessionRow, GuestSessionRow.id == ConsentRow.guest_id)
                .where(
                    GuestSessionRow.expires_at > datetime.now(UTC),
                    GuestSessionRow.state == GuestState.ACTIVE.value,
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
        async with self._sessions() as session:
            subjects = await rewrite_subjects(session, request, guest_id)
        if subjects is None:
            return False
        for subject_id in subjects:
            if not await self.authorized_guest(subject_id, scope=scope):
                return False
        # Every person whose content is sent needs a slot (both people for a Radar pair).
        for subject_id in subjects:
            if not await self.pilot_eligible(subject_id):
                return False
        return True
