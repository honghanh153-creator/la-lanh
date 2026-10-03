from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.domains.content.catalog import (
    activate_daily_catalog,
    bundled_daily_catalog,
    catalog_summary,
)
from app.domains.content.models import (
    ContentChannel,
    ContentRevision,
    ContentRevisionStatus,
    ContentValidationReceipt,
)
from app.domains.content.postgres import PostgresContentRepository
from app.domains.content.review import validate_daily_release
from app.domains.content.validation import validate_daily_catalog
from app.domains.content_rewrite.registry import canonical_surface_registry
from app.domains.content_rewrite.repository import ContentRewriteRepository

logger = logging.getLogger(__name__)


class ContentDraftRejected(ValueError):
    def __init__(self, receipt: ContentValidationReceipt) -> None:
        super().__init__("content draft failed validation")
        self.receipt = receipt


class ContentStudioService:
    def __init__(
        self,
        repository: PostgresContentRepository,
        rewrite_repository: ContentRewriteRepository | None = None,
    ) -> None:
        self._repository = repository
        self._rewrite_repository = rewrite_repository

    async def workspace(self) -> dict[str, Any]:
        channel = await self._repository.get_channel()
        active = (
            await self._repository.get_revision(channel.active_revision_id)
            if channel.active_revision_id is not None
            else None
        )
        payload = active.payload if active is not None else bundled_daily_catalog()
        registry = canonical_surface_registry()
        rewrite_candidates = (
            await self._rewrite_repository.list_review_records()
            if self._rewrite_repository is not None
            else ()
        )
        rewrite_surfaces = [
            {
                "surface": surface.value,
                "fields": list(registry.require(surface).rewritable_fields),
                "schema_version": registry.require(surface).schema_version,
                "gate_version": registry.require(surface).gate_version,
                "forbidden_claims": list(registry.require(surface).forbidden_claims),
                "privacy_manifest": "field names only; request and output values stay encrypted",
            }
            for surface in sorted(registry.surfaces, key=lambda item: item.value)
        ]
        return {
            "channel": channel,
            "active_revision": active,
            "payload": payload,
            "summary": catalog_summary(payload),
            "revisions": await self._repository.list_revisions(),
            "events": await self._repository.list_events(),
            "rewrite_candidates": rewrite_candidates,
            "rewrite_surfaces": rewrite_surfaces,
            "source": "published" if active is not None else "bundled-baseline",
        }

    async def create_draft(
        self,
        payload: dict[str, Any],
        *,
        parent_revision_id: UUID | None,
        request_key: str,
        reason: str,
    ) -> tuple[ContentRevision, ContentValidationReceipt]:
        receipt = validate_daily_release(payload)
        if not receipt.passed:
            raise ContentDraftRejected(receipt)
        revision = await self._repository.create_draft(
            payload,
            parent_revision_id=parent_revision_id,
            request_key=f"draft:{request_key}",
            reason=reason,
        )
        revision = await self._repository.record_validation(
            revision.id,
            receipt,
            request_key=f"validate:{request_key}",
            reason="Automated Content Studio validation",
        )
        return revision, receipt

    async def validate_revision(self, revision_id: UUID) -> ContentValidationReceipt:
        revision = await self._require_revision(revision_id)
        return validate_daily_release(revision.payload)

    async def publish(
        self,
        revision_id: UUID,
        *,
        expected_generation: int,
        request_key: str,
        reason: str,
        rollback: bool = False,
    ) -> tuple[ContentRevision, ContentChannel]:
        revision = await self._require_revision(revision_id)
        receipt = validate_daily_release(revision.payload)
        if not receipt.passed:
            raise ValueError("content revision does not pass current validation")
        if revision.status is not ContentRevisionStatus.PUBLISHED:
            revision = await self._repository.record_validation(
                revision.id,
                receipt,
                request_key=f"publish-validation:{request_key}",
                reason="Fresh validation before activation",
            )
        published = await self._repository.activate(
            revision.id,
            expected_generation=expected_generation,
            request_key=f"activate:{request_key}",
            reason=reason,
            rollback=rollback,
        )
        activate_daily_catalog(revision.payload, generation=published[1].generation)
        return published

    async def activate_published_catalog(self) -> bool:
        """Load the current release into this process, falling back safely."""

        try:
            channel = await self._repository.get_channel()
            if channel.active_revision_id is None:
                return False
            revision = await self._repository.get_revision(channel.active_revision_id)
            if revision is None or revision.contract_version != "daily-content-matrix/v1":
                return False
            receipt = validate_daily_catalog(revision.payload)
            if not receipt.passed:
                return False
            return activate_daily_catalog(revision.payload, generation=channel.generation)
        except Exception:
            logger.warning(
                "Active content release could not be loaded; bundled catalog retained",
                exc_info=True,
            )
            return False

    async def _require_revision(self, revision_id: UUID) -> ContentRevision:
        revision = await self._repository.get_revision(revision_id)
        if revision is None:
            raise LookupError("content revision not found")
        return revision
