from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from app.domains.content_rewrite.models import (
    LeasedRewriteJob,
    RewriteJobResult,
    RewriteRequestEnvelope,
)
from app.domains.content_rewrite.repository import ContentRewriteRepository
from app.domains.content_rewrite.rollout import SurfaceRolloutPolicy
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
from app.infrastructure.generation.pricing import (
    GPT_6_LUNA_STANDARD_2026_10_04,
    GenerationPricing,
    cents_to_nanos,
)
from app.infrastructure.generation.schemas import surface_output_contract

logger = logging.getLogger(__name__)


def reservation_estimate(
    request: RewriteRequestEnvelope,
    pricing: GenerationPricing = GPT_6_LUNA_STANDARD_2026_10_04,
) -> tuple[int, int]:
    """Conservative (tokens, cost nanos) debited before any provider boundary.

    UTF-8 bytes are a deliberate upper bound for prompt tokens; output is the
    surface's hard ``max_output_tokens``. Shared by the worker and any standalone
    paid evaluation so both draw on one ledger with one sizing rule.
    """

    contract = surface_output_contract(request.key.surface)
    input_reserve = (
        len(
            json.dumps(
                request.safe_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        )
        + len(contract.developer_instruction.encode())
        + len(json.dumps(contract.schema, separators=(",", ":")).encode())
        + 512
    )
    output_reserve = contract.max_output_tokens
    cost_nanos = pricing.cost_nanos(input_tokens=input_reserve, output_tokens=output_reserve)
    return input_reserve + output_reserve, cost_nanos


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
        daily_token_budget: int | None = None,
        daily_cost_budget_cents: int | None = None,
        monthly_cost_budget_cents: int | None = None,
        pricing: GenerationPricing = GPT_6_LUNA_STANDARD_2026_10_04,
        rollout: SurfaceRolloutPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._provider = provider
        self._authorization = authorization
        self._projector = projector
        self._lease_seconds = lease_seconds
        self._retry_delay_seconds = retry_delay_seconds
        self._daily_token_budget = daily_token_budget
        self._daily_cost_budget_cents = daily_cost_budget_cents
        self._monthly_cost_budget_cents = monthly_cost_budget_cents
        self._pricing = pricing
        self._rollout = rollout or SurfaceRolloutPolicy.full_for_all()
        self._clock = clock or (lambda: datetime.now(UTC))

    async def process_one(self) -> bool:
        lease = await self._repository.lease(
            now=self._clock(),
            lease_for_seconds=self._lease_seconds,
        )
        if lease is None:
            return False
        if not self._rollout.should_generate(lease.request.key.surface):
            await self._repository.fail(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=RewriteJobResult.DISABLED,
                updated_at=self._clock(),
            )
            return True
        if not await self._authorization.is_authorized(lease.request):
            await self._repository.fail(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=RewriteJobResult.AUTHORIZATION_REVOKED,
                updated_at=self._clock(),
            )
            return True
        reserved_at = self._clock().astimezone(UTC)
        if not await self._reserve_budget(lease, reserved_at):
            await self._repository.fail(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                result=RewriteJobResult.BUDGET_BLOCKED,
                updated_at=self._clock(),
            )
            return True
        await self._execute(lease, reserved_at.date())
        return True

    async def _execute(self, lease: LeasedRewriteJob, reserved_day: date) -> None:
        if self._clock().astimezone(UTC).date() != reserved_day:
            await self._fail(lease, RewriteJobResult.BUDGET_BLOCKED)
            return
        remaining = (lease.lease_expires_at - self._clock()).total_seconds()
        if remaining <= 0:
            await self._fail(lease, RewriteJobResult.AMBIGUOUS)
            return
        async with self._repository.execution_guard(lease) as authorized:
            if not authorized:
                await self._fail(lease, RewriteJobResult.AUTHORIZATION_REVOKED)
                return
            marked = await self._repository.mark_request_started(
                job_id=lease.id,
                lease_token=lease.lease_token,
                deletion_epoch=lease.deletion_epoch,
                started_at=self._clock(),
            )
            if not marked:
                return

        try:
            await self._send_and_publish(lease, reserved_day)
        except Exception:
            # Provider I/O has ended; a failed publication must not prolong erasure.
            await self._repository.finish_send(job_id=lease.id, lease_token=lease.lease_token)
            raise
        else:
            await self._repository.finish_send(job_id=lease.id, lease_token=lease.lease_token)
        # Cancellation/process loss bypasses both branches; the durable fence expires boundedly.

    async def _send_and_publish(self, lease: LeasedRewriteJob, reserved_day: date) -> None:

        # Acquiring locks or writing the send marker can cross UTC midnight.
        # Do not send against yesterday's debit. Keep that debit and never retry.
        if self._clock().astimezone(UTC).date() != reserved_day:
            await self._fail(lease, RewriteJobResult.BUDGET_BLOCKED)
            return

        try:
            # No owner or projector transaction is held while awaiting the provider.
            remaining = (lease.lease_expires_at - self._clock()).total_seconds()
            if remaining <= 0:
                await self._fail(lease, RewriteJobResult.AMBIGUOUS)
                return
            timeout = min(60.0, remaining)
            async with asyncio.timeout(timeout):
                result = await self._provider.generate_rewrite(lease.request)
        except Exception as error:
            logger.error("rewrite provider failed after send marker: %s", type(error).__name__)
            await self._fail(lease, RewriteJobResult.AMBIGUOUS)
            return

        async with self._repository.execution_guard(lease) as authorized:
            completed_at = self._clock()
            if not authorized:
                await self._fail(lease, RewriteJobResult.AUTHORIZATION_REVOKED, completed_at)
            elif isinstance(result, RewriteGenerationSuccess):
                await self._accept(lease, result, completed_at)
            elif isinstance(result, GenerationTransient):
                await self._handle_transient(lease, result, completed_at)
            else:
                await self._fail(lease, _terminal_result(result), completed_at)

    async def _reserve_budget(self, lease: LeasedRewriteJob, now: datetime) -> bool:
        if (
            self._daily_token_budget is None
            and self._daily_cost_budget_cents is None
            and self._monthly_cost_budget_cents is None
        ):
            return True
        if self._daily_token_budget is None or self._daily_cost_budget_cents is None:
            return False
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        requested_tokens, requested_cost_nanos = reservation_estimate(lease.request, self._pricing)
        return await self._repository.reserve_budget(
            job_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            since=day_start,
            requested_tokens=requested_tokens,
            daily_token_limit=self._daily_token_budget,
            requested_cost_nanos=requested_cost_nanos,
            daily_cost_limit_nanos=cents_to_nanos(self._daily_cost_budget_cents),
            pricing_version=self._pricing.version,
            updated_at=now,
            monthly_cost_limit_nanos=(
                cents_to_nanos(self._monthly_cost_budget_cents)
                if self._monthly_cost_budget_cents is not None
                else None
            ),
        )

    async def _accept(
        self,
        lease: LeasedRewriteJob,
        result: RewriteGenerationSuccess,
        completed_at: datetime,
    ) -> None:
        if self._clock() >= lease.lease_expires_at:
            await self._fail(lease, RewriteJobResult.AMBIGUOUS, self._clock())
            return
        if not await self._authorization.is_authorized(lease.request):
            await self._fail(lease, RewriteJobResult.AUTHORIZATION_REVOKED, completed_at)
            return
        if result.key != lease.request.key:
            await self._fail(
                lease,
                RewriteJobResult.PERMANENT,
                completed_at,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_nanos=self._exact_cost(result.input_tokens, result.output_tokens),
            )
            return
        decision = await self._projector.validate_and_project(
            lease.request,
            result.output,
            completed_at=completed_at,
            publish=self._rollout.should_publish(lease.request.key),
        )
        if not decision.accepted or decision.gate_receipt_id is None:
            await self._fail(
                lease,
                RewriteJobResult.GATE_REJECTED,
                completed_at,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_nanos=self._exact_cost(result.input_tokens, result.output_tokens),
            )
            return
        canonical = json.dumps(
            result.output,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        finalized = await self._repository.succeed(
            lease=lease,
            gate_receipt_id=decision.gate_receipt_id,
            output_fingerprint=sha256(canonical.encode()).hexdigest(),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_nanos=self._exact_cost(result.input_tokens, result.output_tokens),
            completed_at=self._clock(),
        )
        if not finalized:
            # Roll back all borrowed projector writes instead of exposing an unowned result.
            raise RuntimeError("rewrite lease was lost before atomic publication")

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
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_nanos: int | None = None,
    ) -> None:
        await self._repository.fail(
            job_id=lease.id,
            lease_token=lease.lease_token,
            deletion_epoch=lease.deletion_epoch,
            result=result,
            updated_at=completed_at or self._clock(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_nanos=cost_nanos,
        )

    def _exact_cost(self, input_tokens: int | None, output_tokens: int | None) -> int | None:
        if input_tokens is None or output_tokens is None:
            return None
        return self._pricing.cost_nanos(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
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
    from app.domains.content_rewrite.rollout import SurfaceRolloutPolicy
    from app.domains.content_rewrite.service import RewriteProjectorRouter
    from app.domains.radar.rewrite import RadarRewriteProjector
    from app.domains.readings.postgres import PostgresReadingRepository
    from app.domains.readings.rewrite import ReadingRewriteProjector
    from app.domains.tarot.rewrite import TarotRewriteProjector
    from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider, decode_key
    from app.infrastructure.generation import build_rewrite_generation_provider

    settings = get_settings()
    if not settings.generation_worker_enabled:
        return
    database = Database(str(settings.database_url))
    await database.initialize()
    envelope = AesGcmEnvelopeCipher(
        StaticDataKeyProvider(
            decode_key(settings.guest_encryption_key.get_secret_value(), expected_bytes=32)
        )
    )
    authorization = DatabaseRewriteAuthorization(
        database.sessions, pilot_user_limit=settings.generation_pilot_user_limit
    )
    reading_projector = ReadingRewriteProjector(
        PostgresReadingRepository(database.sessions, envelope)
    )
    projector = RewriteProjectorRouter(
        {
            RewriteSurface.DAILY_HOME: reading_projector,
            RewriteSurface.REVEAL: reading_projector,
            RewriteSurface.NATAL: reading_projector,
            RewriteSurface.TRANSIT_INSIGHT: reading_projector,
            RewriteSurface.RADAR: RadarRewriteProjector(database.sessions, envelope),
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
        daily_token_budget=settings.generation_daily_token_budget,
        daily_cost_budget_cents=settings.generation_daily_budget_cents,
        monthly_cost_budget_cents=settings.generation_monthly_budget_cents,
        rollout=SurfaceRolloutPolicy.from_settings(settings.generation_surface_rollout),
    )
    try:
        await worker.run_forever()
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(_run_standalone())


if __name__ == "__main__":
    main()
