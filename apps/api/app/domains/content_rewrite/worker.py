from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.domains.content_rewrite.models import (
    LeasedRewriteJob,
    RewriteJobResult,
)
from app.domains.content_rewrite.repository import ContentRewriteRepository
from app.domains.content_rewrite.service import RewriteAuthorizationChecker, RewriteProjector
from app.infrastructure.generation.base import (
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationRefusal,
    GenerationTransient,
    RewriteGenerationProvider,
    RewriteGenerationSuccess,
)

logger = logging.getLogger(__name__)


class ContentRewriteWorker:
    def __init__(
        self,
        repository: ContentRewriteRepository,
        provider: RewriteGenerationProvider,
        authorization: RewriteAuthorizationChecker,
        projector: RewriteProjector,
        *,
        lease_seconds: int = 120,
        retry_delay_seconds: int = 60,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._provider = provider
        self._authorization = authorization
        self._projector = projector
        self._lease_seconds = lease_seconds
        self._retry_delay_seconds = retry_delay_seconds
        self._clock = clock or (lambda: datetime.now(UTC))

    async def process_one(self) -> bool:
        lease = await self._repository.lease(
            now=self._clock(),
            lease_for_seconds=self._lease_seconds,
        )
        if lease is None:
            return False
        if not await self._authorization.is_authorized(lease.request):
            await self._repository.fail(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=RewriteJobResult.AUTHORIZATION_REVOKED,
                updated_at=self._clock(),
            )
            return True
        marked = await self._repository.mark_request_started(
            job_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            started_at=self._clock(),
        )
        if not marked:
            return True

        try:
            result = await self._provider.generate_rewrite(lease.request)
        except Exception as error:
            logger.error("rewrite provider failed after send marker: %s", type(error).__name__)
            await self._fail(lease, RewriteJobResult.AMBIGUOUS)
            return True

        completed_at = self._clock()
        if isinstance(result, RewriteGenerationSuccess):
            await self._accept(lease, result, completed_at)
        elif isinstance(result, GenerationTransient):
            await self._handle_transient(lease, result, completed_at)
        else:
            await self._fail(lease, _terminal_result(result), completed_at)
        return True

    async def _accept(
        self,
        lease: LeasedRewriteJob,
        result: RewriteGenerationSuccess,
        completed_at: datetime,
    ) -> None:
        if result.key != lease.request.key:
            await self._fail(lease, RewriteJobResult.PERMANENT, completed_at)
            return
        decision = await self._projector.validate_and_project(
            lease.request,
            result.output,
            completed_at=completed_at,
        )
        if not decision.accepted or decision.gate_receipt_id is None:
            await self._fail(lease, RewriteJobResult.GATE_REJECTED, completed_at)
            return
        canonical = json.dumps(
            result.output,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        await self._repository.succeed(
            lease=lease,
            gate_receipt_id=decision.gate_receipt_id,
            output_fingerprint=sha256(canonical.encode()).hexdigest(),
            completed_at=completed_at,
        )

    async def _handle_transient(
        self,
        lease: LeasedRewriteJob,
        result: GenerationTransient,
        completed_at: datetime,
    ) -> None:
        if result.retry_safe and lease.attempt_count < lease.max_attempts:
            await self._repository.retry(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=RewriteJobResult.TRANSIENT,
                next_attempt_at=completed_at + timedelta(seconds=self._retry_delay_seconds),
                updated_at=completed_at,
            )
            return
        await self._fail(
            lease,
            RewriteJobResult.TRANSIENT if result.retry_safe else RewriteJobResult.AMBIGUOUS,
            completed_at,
        )

    async def _fail(
        self,
        lease: LeasedRewriteJob,
        result: RewriteJobResult,
        completed_at: datetime | None = None,
    ) -> None:
        await self._repository.fail(
            job_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            result=result,
            updated_at=completed_at or self._clock(),
        )

    async def run_forever(self, *, poll_seconds: float = 2.0) -> None:
        failure_delay = poll_seconds
        while True:
            try:
                processed = await self.process_one()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.error("content rewrite worker iteration failed: %s", type(error).__name__)
                await asyncio.sleep(failure_delay)
                failure_delay = min(max(poll_seconds, failure_delay * 2), 30.0)
                continue
            failure_delay = poll_seconds
            if not processed:
                await asyncio.sleep(poll_seconds)


def _terminal_result(
    result: GenerationRefusal | GenerationIncomplete | GenerationPermanent | GenerationDisabled,
) -> RewriteJobResult:
    if isinstance(result, GenerationRefusal):
        return RewriteJobResult.REFUSAL
    if isinstance(result, GenerationIncomplete):
        return RewriteJobResult.INCOMPLETE
    if isinstance(result, GenerationDisabled):
        return RewriteJobResult.DISABLED
    return RewriteJobResult.PERMANENT


async def _run_standalone() -> None:
    from app.config import get_settings
    from app.db.session import Database
    from app.domains.content_rewrite.authorization import DatabaseRewriteAuthorization
    from app.domains.content_rewrite.models import RewriteSurface
    from app.domains.content_rewrite.postgres import PostgresContentRewriteRepository
    from app.domains.content_rewrite.service import RewriteProjectorRouter
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.rewrite import ReadingRewriteProjector
    from app.domains.tarot.rewrite import TarotRewriteProjector
    from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider, decode_key
    from app.infrastructure.generation import build_rewrite_generation_provider

    settings = get_settings()
    if not settings.generation_enabled:
        return
    database = Database(str(settings.database_url))
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(
        StaticDataKeyProvider(
            decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
        )
    )
    authorization = DatabaseRewriteAuthorization(database.sessions)
    reading_projector = ReadingRewriteProjector(
        PostgresReadingRepository(database.sessions, envelope)
    )
    projector = RewriteProjectorRouter(
        {
            RewriteSurface.DAILY_HOME: reading_projector,
            RewriteSurface.REVEAL: reading_projector,
            RewriteSurface.NATAL: reading_projector,
            RewriteSurface.TRANSIT_INSIGHT: reading_projector,
            RewriteSurface.TAROT: TarotRewriteProjector(database.sessions, envelope),
        }
    )
    worker = ContentRewriteWorker(
        PostgresContentRewriteRepository(database.sessions, envelope),
        build_rewrite_generation_provider(settings),
        authorization,
        projector,
        lease_seconds=settings.generation_lease_seconds,
        retry_delay_seconds=settings.generation_retry_delay_seconds,
    )
    try:
        await worker.run_forever()
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(_run_standalone())


if __name__ == "__main__":
    main()
