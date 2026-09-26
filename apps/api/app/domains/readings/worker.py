from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.config import get_settings
from app.db.session import Database
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    GenerationAttemptResult,
    LeasedGenerationAttempt,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_gate_policy_version,
    canonical_reading_revision_key,
)
from app.domains.readings.postgres import PostgresReadingRepository
from app.domains.readings.repository import GenerationWorkerRepository
from app.infrastructure.crypto import (
    AesGcmEnvelopeCipher,
    StaticDataKeyProvider,
    decode_key,
)
from app.infrastructure.generation import build_generation_provider
from app.infrastructure.generation.base import (
    GenerationDisabled,
    GenerationIncomplete,
    GenerationPermanent,
    GenerationProvider,
    GenerationRefusal,
    GenerationSuccess,
    GenerationTransient,
)

logger = logging.getLogger(__name__)


class ReadingGenerationWorker:
    def __init__(
        self,
        repository: GenerationWorkerRepository,
        provider: GenerationProvider,
        *,
        lease_seconds: int = 120,
        retry_delay_seconds: int = 60,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._provider = provider
        self._lease_seconds = lease_seconds
        self._retry_delay_seconds = retry_delay_seconds
        self._clock = clock or (lambda: datetime.now(UTC))

    async def process_one(self) -> bool:
        lease = await self._repository.lease_generation_attempt(
            now=self._clock(),
            lease_for_seconds=self._lease_seconds,
        )
        if lease is None:
            return False
        started_at = self._clock()
        marked = await self._repository.mark_generation_request_started(
            attempt_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            started_at=started_at,
        )
        if not marked:
            return True

        # This is deliberately the only network await and occurs after every DB
        # context above has committed and closed.
        try:
            result = await self._provider.generate(lease.plan_record.plan)
        except Exception as error:
            # Delivery may have started. Close the durable attempt as ambiguous and
            # never retry it from this process boundary.
            logger.error(
                "reading generation provider failed after send marker: %s",
                type(error).__name__,
            )
            await self._repository.fail_generation_attempt(
                attempt_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=GenerationAttemptResult.AMBIGUOUS,
                updated_at=self._clock(),
            )
            return True
        completed_at = self._clock()
        if isinstance(result, GenerationSuccess):
            await self._accept_success(lease, result, completed_at)
        elif isinstance(result, GenerationTransient):
            await self._handle_transient(lease, result, completed_at)
        else:
            await self._repository.fail_generation_attempt(
                attempt_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=_terminal_result(result),
                updated_at=completed_at,
            )
        return True

    async def _accept_success(
        self,
        lease: LeasedGenerationAttempt,
        result: GenerationSuccess,
        completed_at: datetime,
    ) -> None:
        candidate = result.candidate
        evaluation = evaluate_candidate(lease.plan_record.plan, candidate)
        if not evaluation.accepted or evaluation.publishable_candidate is None:
            await self._repository.fail_generation_attempt(
                attempt_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=GenerationAttemptResult.GATE_REJECTED,
                updated_at=completed_at,
            )
            return
        gate_policy_version = canonical_gate_policy_version(evaluation)
        content_version = f"generated-{lease.generation_key[:16]}"
        source = ReadingRevisionSource.GENERATED
        revision = ReadingRevisionRecord(
            id=uuid4(),
            guest_id=lease.plan_record.guest_id,
            profile_id=lease.plan_record.profile_id,
            plan_id=lease.plan_record.id,
            revision_key=canonical_reading_revision_key(
                plan_key=lease.plan_record.plan_key,
                source=source,
                renderer_version=candidate.renderer_version,
                content_version=content_version,
                schema_version=candidate.schema_version,
                rules_version=lease.plan_record.plan.rules_version,
                gate_policy_version=gate_policy_version,
            ),
            source=source,
            renderer_version=candidate.renderer_version,
            content_version=content_version,
            schema_version=candidate.schema_version,
            rules_version=lease.plan_record.plan.rules_version,
            gate_policy_version=gate_policy_version,
            evaluation=evaluation,
            created_at=completed_at,
        )
        await self._repository.finalize_generation_success(
            lease=lease,
            revision=revision,
            completed_at=completed_at,
        )

    async def _handle_transient(
        self,
        lease: LeasedGenerationAttempt,
        result: GenerationTransient,
        completed_at: datetime,
    ) -> None:
        if result.retry_safe and lease.attempt_count < lease.max_attempts:
            await self._repository.retry_generation_attempt(
                attempt_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=GenerationAttemptResult.TRANSIENT,
                next_attempt_at=completed_at + timedelta(seconds=self._retry_delay_seconds),
                updated_at=completed_at,
            )
            return
        await self._repository.fail_generation_attempt(
            attempt_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            result=(
                GenerationAttemptResult.TRANSIENT
                if result.retry_safe
                else GenerationAttemptResult.AMBIGUOUS
            ),
            updated_at=completed_at,
        )

    async def run_forever(self, *, poll_seconds: float = 2.0) -> None:
        failure_delay = poll_seconds
        while True:
            try:
                processed = await self.process_one()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.error(
                    "reading generation worker iteration failed: %s",
                    type(error).__name__,
                )
                await asyncio.sleep(failure_delay)
                failure_delay = min(max(poll_seconds, failure_delay * 2), 30.0)
                continue
            failure_delay = poll_seconds
            if not processed:
                await asyncio.sleep(poll_seconds)


def _terminal_result(
    result: GenerationRefusal | GenerationIncomplete | GenerationPermanent | GenerationDisabled,
) -> GenerationAttemptResult:
    if isinstance(result, GenerationRefusal):
        return GenerationAttemptResult.REFUSAL
    if isinstance(result, GenerationIncomplete):
        return GenerationAttemptResult.INCOMPLETE
    if isinstance(result, GenerationDisabled):
        return GenerationAttemptResult.DISABLED
    return GenerationAttemptResult.PERMANENT


async def _run_standalone() -> None:
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
    repository = PostgresReadingRepository(database.sessions, envelope)
    worker = ReadingGenerationWorker(
        repository,
        build_generation_provider(settings),
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
