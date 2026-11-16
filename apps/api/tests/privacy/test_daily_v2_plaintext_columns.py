"""PV-6 guard: Daily v2 fields stay inside the encrypted envelope.

Daily v2 situation, rotation and scene choices are derived from the owner's chart
and day. They live only in ``reading_plans.plan_ciphertext`` (the frozen plan),
``reading_revisions.evaluation_ciphertext`` (the rendered candidate) and
``daily_notes.content_ciphertext`` (the note prose). This test pins the plaintext
column set of every table that stores Daily data, so a new readable column fails
here until it is reviewed and either encrypted or added to the allowlist with a
reason.
"""

from pydantic import BaseModel

from app.db.base import Base
from app.domains.readings.models import (
    DailyMeaningBrief,
    DailySelection,
    DailyVariety,
    ReadingPlan,
    SemanticBlueprint,
)

# Column -> why it is safe to keep readable. Ciphertext columns are listed too so
# the set is exact; their value is never readable without the data key.
DAILY_STORAGE_COLUMNS: dict[str, dict[str, str]] = {
    "daily_notes": {
        "id": "row id",
        "guest_id": "owner key for authorization",
        "note_date": "calendar day of the note, needed for one-note-per-day",
        "title": "legacy column, written empty since content moved to ciphertext",
        "body": "legacy column, written empty since content moved to ciphertext",
        "full_body": "legacy column, written empty since content moved to ciphertext",
        "context_label": "legacy column, written empty since content moved to ciphertext",
        "content_ciphertext": "encrypted note content",
        "content_version": "release version string",
        "persona_mode": "closed enum, tracked as PV-26",
        "persona_label": "closed enum, tracked as PV-26",
        "persona_version": "release version string",
        "source_level": "closed enum of data completeness",
        "astrology_source_version": "engine version string",
        "fallback_used": "boolean",
        "fallback_reason": "closed enum",
        "chart_snapshot_id": "foreign key, no chart value",
        "created_at": "timestamp",
    },
    "daily_experiments": {
        "id": "row id",
        "version": "optimistic lock counter",
        "guest_id": "owner key for authorization",
        "daily_note_id": "foreign key",
        "revision_id": "foreign key",
        "state": "closed enum",
        "payload_ciphertext": "encrypted experiment payload",
        "created_at": "timestamp",
        "updated_at": "timestamp",
        "expires_at": "timestamp",
        "reflected_at": "timestamp",
    },
    "reading_plans": {
        "id": "row id",
        "guest_id": "owner key for authorization",
        "profile_id": "owner key for authorization",
        "chart_snapshot_id": "foreign key, no chart value",
        "plan_key": "SHA-256 identity bound to the snapshot id",
        "plan_ciphertext": "encrypted plan, holds every Daily v2 field",
        "created_at": "timestamp",
    },
    "reading_revisions": {
        "id": "row id",
        "guest_id": "owner key for authorization",
        "profile_id": "owner key for authorization",
        "plan_id": "foreign key",
        "revision_key": "SHA-256 identity",
        "source": "closed enum",
        "renderer_version": "release version string",
        "content_version": "release version string",
        "schema_version": "release version string",
        "rules_version": "release version string",
        "gate_policy_version": "gate names and versions",
        "accepted": "boolean",
        "evaluation_ciphertext": "encrypted candidate and gate reports",
        "created_at": "timestamp",
    },
    "reading_projections": {
        "id": "row id",
        "guest_id": "owner key for authorization",
        "profile_id": "owner key for authorization",
        "scope_key": "SHA-256 identity",
        "purpose": "closed enum",
        "tradition": "closed enum",
        "config_hash": "calculation settings hash, no chart value",
        "lens_variant": "SHA-256 of a closed lens enum",
        "local_date": "calendar day of the reading",
        "timezone_name": "IANA zone used for the day boundary",
        "observed_at": "timestamp",
        "active_revision_id": "foreign key",
        "available_revision_id": "foreign key",
        "acknowledged_aura_transition_id": "SHA-256 identity",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
    "reading_generation_attempts": {
        "id": "row id",
        "guest_id": "owner key for authorization",
        "profile_id": "owner key for authorization",
        "plan_id": "foreign key",
        "scope_key": "SHA-256 identity",
        "generation_key": "SHA-256 identity",
        "provider": "provider name",
        "model": "model name",
        "prompt_version": "release version string",
        "deletion_epoch": "random erasure fence",
        "status": "closed enum",
        "lease_token": "random lease id",
        "lease_expires_at": "timestamp",
        "request_started_at": "timestamp",
        "attempt_count": "counter",
        "max_attempts": "counter",
        "next_attempt_at": "timestamp",
        "accepted_revision_id": "foreign key",
        "last_result": "closed enum",
        "created_at": "timestamp",
        "updated_at": "timestamp",
    },
}

# Generic names that also exist as unrelated columns (row lock counters).
_GENERIC_FIELD_NAMES = frozenset({"version"})


def _field_names(*models: type[BaseModel]) -> frozenset[str]:
    return frozenset(name for model in models for name in model.model_fields)


def _daily_v2_field_names() -> frozenset[str]:
    plan_fields = {"daily_selection", "daily_variety", "semantic_blueprint"}
    assert {"daily_selection", "daily_variety"} <= set(ReadingPlan.model_fields)
    return (
        _field_names(DailySelection, DailyVariety, SemanticBlueprint, DailyMeaningBrief)
        | plan_fields
    ) - _GENERIC_FIELD_NAMES


def test_daily_storage_tables_have_only_reviewed_plaintext_columns() -> None:
    for table_name, allowed in DAILY_STORAGE_COLUMNS.items():
        table = Base.metadata.tables[table_name]
        actual = {column.name for column in table.columns}
        assert actual == set(allowed), (
            f"{table_name} columns changed: added {sorted(actual - set(allowed))}, "
            f"removed {sorted(set(allowed) - actual)}. Daily v2 fields belong inside the "
            "encrypted envelope; add a plaintext column here only after privacy review."
        )


def test_no_table_stores_a_daily_v2_field_as_its_own_column() -> None:
    v2_fields = _daily_v2_field_names()
    assert {"issue_key", "seed", "scene_key", "daily_selection", "daily_variety"} <= v2_fields
    leaked = sorted(
        f"{table.name}.{column.name}"
        for table in Base.metadata.sorted_tables
        for column in table.columns
        if column.name in v2_fields
    )
    assert leaked == []
