from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, text
from sqlalchemy.dialects import postgresql

from app.db.session import Database
from app.domains.astro.models import DateOnlySunResult, EngineProvenance, Tradition, ZodiacSign
from app.domains.birth.tables import BirthProfileRow
from app.domains.guest.tables import GuestSessionRow
from app.domains.readings.gates import evaluate_candidate
from app.domains.readings.models import (
    BackgroundLens,
    ReadingPlan,
    ReadingPlanRecord,
    ReadingProjectionRecord,
    ReadingPurpose,
    ReadingRevisionRecord,
    ReadingRevisionSource,
    canonical_gate_policy_version,
    canonical_lens_variant,
    canonical_projection_scope_key,
    canonical_reading_plan_key,
    canonical_reading_revision_key,
)
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.postgres import (
    ImmutableReadingConflictError,
    PostgresReadingRepository,
    ReadingOwnershipError,
    _profile_for_activation_query,
)
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.infrastructure.crypto import AesGcmEnvelopeCipher, StaticDataKeyProvider

NOW = datetime(2026, 9, 7, 12, tzinfo=UTC)


@pytest.fixture
async def storage(tmp_path):  # type: ignore[no-untyped-def]
    database = Database(f"sqlite+aiosqlite:///{tmp_path / 'readings.db'}")
    await database.initialize()
    repository = PostgresReadingRepository(
        database.sessions,
        AesGcmEnvelopeCipher(StaticDataKeyProvider(b"r" * 32)),
    )
    try:
        yield database, repository
    finally:
        await database.dispose()


async def _owner(database: Database) -> tuple[UUID, UUID]:
    guest_id = uuid4()
    profile_id = uuid4()
    async with database.sessions() as session, session.begin():
        guest = GuestSessionRow(
            id=guest_id,
            token_hash=uuid4().bytes + uuid4().bytes,
            csrf_hash=uuid4().bytes + uuid4().bytes,
            state="active",
            onboarding_status="birth_ready",
            created_at=NOW,
            last_active_at=NOW,
            expires_at=NOW + timedelta(days=30),
        )
        session.add(guest)
        await session.flush([guest])
        session.add(
            BirthProfileRow(
                id=profile_id,
                guest_id=guest_id,
                current_snapshot_id=None,
                profile_level=1,
                time_precision="unknown",
                created_at=NOW,
                updated_at=NOW,
            )
        )
    return guest_id, profile_id


def _plan() -> ReadingPlan:
    date_only = DateOnlySunResult(
        status="certain",
        sign=ZodiacSign.PISCES,
        candidates=(ZodiacSign.PISCES,),
        provenance=EngineProvenance(version="2.10.03", profile="test"),
    )
    return ReadingPlanner().plan(date_only, purpose=ReadingPurpose.DAILY_NOTE)


def _plan_record(guest_id: UUID, profile_id: UUID) -> ReadingPlanRecord:
    plan = _plan()
    return ReadingPlanRecord(
        id=uuid4(),
        guest_id=guest_id,
        profile_id=profile_id,
        chart_snapshot_id=None,
        plan_key=canonical_reading_plan_key(plan),
        plan=plan,
        created_at=NOW,
    )


def _revision_record(
    plan_record: ReadingPlanRecord,
    *,
    content_version: str = "daily-note-v1",
    source: ReadingRevisionSource = ReadingRevisionSource.DETERMINISTIC,
) -> ReadingRevisionRecord:
    candidate = DeterministicVietnameseRenderer().render(plan_record.plan)
    evaluation = evaluate_candidate(plan_record.plan, candidate)
    gate_policy_version = canonical_gate_policy_version(evaluation)
    return ReadingRevisionRecord(
        id=uuid4(),
        guest_id=plan_record.guest_id,
        profile_id=plan_record.profile_id,
        plan_id=plan_record.id,
        revision_key=canonical_reading_revision_key(
            plan_key=plan_record.plan_key,
            source=source,
            renderer_version=candidate.renderer_version,
            content_version=content_version,
            schema_version=candidate.schema_version,
            rules_version=plan_record.plan.rules_version,
            gate_policy_version=gate_policy_version,
        ),
        source=source,
        renderer_version=candidate.renderer_version,
        content_version=content_version,
        schema_version=candidate.schema_version,
        rules_version=plan_record.plan.rules_version,
        gate_policy_version=gate_policy_version,
        evaluation=evaluation,
        created_at=NOW,
    )


def _projection_record(guest_id: UUID, profile_id: UUID) -> ReadingProjectionRecord:
    config_hash = _plan().config_hash
    scope_key = canonical_projection_scope_key(
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        config_hash=config_hash,
        local_date=date(2026, 9, 7),
        timezone_name="Asia/Ho_Chi_Minh",
        observed_at=NOW,
    )
    return ReadingProjectionRecord(
        id=uuid4(),
        guest_id=guest_id,
        profile_id=profile_id,
        scope_key=scope_key,
        purpose=ReadingPurpose.DAILY_NOTE,
        tradition=Tradition.WESTERN,
        config_hash=config_hash,
        local_date=date(2026, 9, 7),
        timezone_name="Asia/Ho_Chi_Minh",
        observed_at=NOW,
        active_revision_id=None,
        available_revision_id=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_context_projection_scope_is_opaque_distinct_and_auto_compatible() -> None:
    def scope(lens_variant: str | None = None) -> str:
        return canonical_projection_scope_key(
            purpose=ReadingPurpose.DAILY_NOTE,
            tradition=Tradition.WESTERN,
            config_hash=_plan().config_hash,
            local_date=date(2026, 9, 7),
            timezone_name="Asia/Ho_Chi_Minh",
            observed_at=NOW,
            lens_variant=lens_variant,
        )

    legacy_auto = scope()
    explicit_auto = scope(None)
    relationships_variant = canonical_lens_variant(BackgroundLens.RELATIONSHIPS)
    relationships = scope(relationships_variant)

    assert explicit_auto == legacy_auto
    assert relationships != legacy_auto
    assert relationships_variant is not None
    assert relationships_variant != BackgroundLens.RELATIONSHIPS.value


async def test_plan_and_revision_are_encrypted_and_idempotently_replayed(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    plan = _plan_record(guest_id, profile_id)

    stored_plan, replayed = await repository.save_or_replay_plan(plan)
    revision = _revision_record(stored_plan)
    stored_revision, revision_replayed = await repository.save_or_replay_revision(revision)

    assert replayed is False
    assert revision_replayed is False
    assert (await repository.save_or_replay_plan(plan.model_copy(update={"id": uuid4()})))[
        1
    ] is True
    assert (await repository.save_or_replay_revision(revision.model_copy(update={"id": uuid4()})))[
        1
    ] is True
    assert stored_revision.evaluation.publishable_candidate is not None

    async with database.sessions() as session:
        plan_ciphertext = await session.scalar(text("SELECT plan_ciphertext FROM reading_plans"))
        evaluation_ciphertext = await session.scalar(
            text("SELECT evaluation_ciphertext FROM reading_revisions")
        )
    assert isinstance(plan_ciphertext, str) and plan_ciphertext.startswith("aesgcm:")
    assert isinstance(evaluation_ciphertext, str) and evaluation_ciphertext.startswith("aesgcm:")
    assert "song ngư" not in plan_ciphertext.lower()
    assert "giờ sinh chính xác" not in evaluation_ciphertext.lower()


async def test_same_immutable_key_with_changed_payload_is_rejected(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    plan = _plan_record(guest_id, profile_id)
    await repository.save_or_replay_plan(plan)

    conflicting_plan = plan.model_copy(
        update={"plan": plan.plan.model_copy(update={"allowed_language": ("khác",)})}
    )
    with pytest.raises(ImmutableReadingConflictError):
        await repository.save_or_replay_plan(conflicting_plan)

    revision = _revision_record(plan)
    await repository.save_or_replay_revision(revision)
    assert revision.evaluation.publishable_candidate is not None
    changed_evaluation = revision.evaluation.model_copy(
        update={
            "publishable_candidate": revision.evaluation.publishable_candidate.model_copy(
                update={"micro_action": "Một nội dung khác nhưng dùng lại cùng khóa."}
            )
        }
    )
    conflicting_revision = revision.model_copy(update={"evaluation": changed_evaluation})
    with pytest.raises(ImmutableReadingConflictError):
        await repository.save_or_replay_revision(conflicting_revision)


def test_rejected_candidate_cannot_become_an_immutable_revision() -> None:
    plan = _plan_record(uuid4(), uuid4())
    revision = _revision_record(plan)
    candidate = (
        DeterministicVietnameseRenderer()
        .render(plan.plan)
        .model_copy(update={"manifestation": "Ngày 21/09/2026 góc này sẽ kết thúc."})
    )
    rejected = evaluate_candidate(plan.plan, candidate)
    assert rejected.accepted is False
    payload = revision.model_dump()
    payload["evaluation"] = rejected

    with pytest.raises(ValidationError, match="only accepted evaluations"):
        ReadingRevisionRecord.model_validate(payload)


def test_projection_scope_rejects_a_local_date_from_another_timezone_day() -> None:
    with pytest.raises(ValueError, match="local_date must match"):
        canonical_projection_scope_key(
            purpose=ReadingPurpose.DAILY_NOTE,
            tradition=Tradition.WESTERN,
            config_hash=_plan().config_hash,
            local_date=date(2026, 9, 7),
            timezone_name="Asia/Ho_Chi_Minh",
            observed_at=datetime(2026, 9, 7, 18, tzinfo=UTC),
        )


def test_activation_locks_birth_profile_before_snapshot_comparison() -> None:
    statement = _profile_for_activation_query(uuid4(), uuid4())
    compiled = str(statement.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]

    assert "FROM birth_profiles" in compiled
    assert "FOR UPDATE" in compiled


async def test_new_revision_waits_for_explicit_activation(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    plan = _plan_record(guest_id, profile_id)
    await repository.save_or_replay_plan(plan)
    first, _ = await repository.save_or_replay_revision(_revision_record(plan))
    second, _ = await repository.save_or_replay_revision(
        _revision_record(plan, content_version="daily-note-v2")
    )
    projection, _ = await repository.get_or_create_projection(
        _projection_record(guest_id, profile_id)
    )

    projection = await repository.publish_available(
        guest_id, profile_id, projection.scope_key, first.id
    )
    assert projection.active_revision_id == first.id
    assert projection.available_revision_id is None

    projection = await repository.publish_available(
        guest_id, profile_id, projection.scope_key, second.id
    )
    assert projection.active_revision_id == first.id
    assert projection.available_revision_id == second.id

    stale = await repository.activate_available(
        guest_id,
        profile_id,
        projection.scope_key,
        expected_revision_id=first.id,
        updated_at=NOW + timedelta(seconds=30),
    )
    assert stale is None
    unchanged = await repository.get_projection(guest_id, profile_id, projection.scope_key)
    assert unchanged is not None
    assert unchanged.active_revision_id == first.id
    assert unchanged.available_revision_id == second.id

    activated = await repository.activate_available(
        guest_id,
        profile_id,
        projection.scope_key,
        expected_revision_id=second.id,
        updated_at=NOW + timedelta(minutes=1),
    )
    assert activated is not None
    assert activated.active_revision_id == second.id
    assert activated.available_revision_id is None


async def test_database_stores_auto_and_context_projection_without_collision(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    automatic = _projection_record(guest_id, profile_id)
    variant = canonical_lens_variant(BackgroundLens.WORK)
    assert variant is not None
    contextual = automatic.model_copy(
        update={
            "id": uuid4(),
            "scope_key": canonical_projection_scope_key(
                purpose=automatic.purpose,
                tradition=automatic.tradition,
                config_hash=automatic.config_hash,
                local_date=automatic.local_date,
                timezone_name=automatic.timezone_name,
                observed_at=automatic.observed_at,
                lens_variant=variant,
            ),
            "lens_variant": variant,
        }
    )

    first, first_replay = await repository.get_or_create_projection(automatic)
    second, second_replay = await repository.get_or_create_projection(contextual)

    assert first_replay is second_replay is False
    assert first.scope_key != second.scope_key
    assert first.lens_variant is None
    assert second.lens_variant == variant
    async with database.sessions() as session:
        stored = (
            await session.execute(
                text(
                    "SELECT scope_key, lens_variant FROM reading_projections ORDER BY lens_variant"
                )
            )
        ).all()
    assert len(stored) == 2
    assert {row.lens_variant for row in stored} == {None, variant}


async def test_refetch_does_not_offer_deterministic_fallback_after_generated_activation(
    storage: tuple[Database, PostgresReadingRepository],
) -> None:
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    plan = _plan_record(guest_id, profile_id)
    await repository.save_or_replay_plan(plan)
    fallback, _ = await repository.save_or_replay_revision(_revision_record(plan))
    generated, _ = await repository.save_or_replay_revision(
        _revision_record(
            plan,
            content_version="daily-note-generated-v1",
            source=ReadingRevisionSource.GENERATED,
        )
    )
    projection, _ = await repository.get_or_create_projection(
        _projection_record(guest_id, profile_id)
    )

    projection = await repository.publish_available(
        guest_id, profile_id, projection.scope_key, fallback.id
    )
    projection = await repository.publish_available(
        guest_id, profile_id, projection.scope_key, generated.id
    )
    activated = await repository.activate_available(
        guest_id,
        profile_id,
        projection.scope_key,
        expected_revision_id=generated.id,
        updated_at=NOW + timedelta(minutes=1),
    )
    assert activated is not None

    refreshed = await repository.publish_available(
        guest_id, profile_id, projection.scope_key, fallback.id
    )

    assert refreshed.active_revision_id == generated.id
    assert refreshed.available_revision_id is None


async def test_ownership_isolation_and_cross_profile_pointer_rejection(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_a, profile_a = await _owner(database)
    guest_b, profile_b = await _owner(database)
    plan_a = _plan_record(guest_a, profile_a)
    plan_b = _plan_record(guest_b, profile_b)
    await repository.save_or_replay_plan(plan_a)
    await repository.save_or_replay_plan(plan_b)
    revision_b, _ = await repository.save_or_replay_revision(_revision_record(plan_b))
    projection_a, _ = await repository.get_or_create_projection(
        _projection_record(guest_a, profile_a)
    )

    assert await repository.get_revision(guest_a, profile_a, revision_b.id) is None
    assert await repository.get_projection(guest_b, profile_b, projection_a.scope_key) is None
    with pytest.raises(ReadingOwnershipError):
        await repository.publish_available(
            guest_a, profile_a, projection_a.scope_key, revision_b.id
        )


async def test_guest_deletion_cascades_all_reading_storage(storage) -> None:  # type: ignore[no-untyped-def]
    database, repository = storage
    guest_id, profile_id = await _owner(database)
    plan = _plan_record(guest_id, profile_id)
    await repository.save_or_replay_plan(plan)
    revision, _ = await repository.save_or_replay_revision(_revision_record(plan))
    projection, _ = await repository.get_or_create_projection(
        _projection_record(guest_id, profile_id)
    )
    await repository.publish_available(guest_id, profile_id, projection.scope_key, revision.id)

    async with database.sessions() as session, session.begin():
        await session.execute(delete(GuestSessionRow).where(GuestSessionRow.id == guest_id))
    async with database.sessions() as session:
        counts_list: list[int] = []
        for table in ("reading_plans", "reading_revisions", "reading_projections"):
            count = await session.scalar(
                text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - closed test table list
            )
            counts_list.append(int(count or 0))
        counts = tuple(counts_list)
    assert counts == (0, 0, 0)
