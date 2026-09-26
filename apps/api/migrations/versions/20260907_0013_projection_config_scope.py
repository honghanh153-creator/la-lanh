"""Bind reading projections to their calculation configuration.

Revision ID: 20260907_0013
Revises: 20260907_0012

Legacy rows are backfilled only when a linked active/available revision leads to a
legacy plaintext chart snapshot with an explicit config hash. Encrypted or unlinked
rows require a key-aware operational backfill that decrypts ReadingPlan, splits any
mixed-config pointer state, and computes the canonical scope key. The migration is a
No-Go while any such row remains; it never invents a configuration hash.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0013"
down_revision: str | None = "20260907_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BACKFILL_CONFIG_HASH = sa.text(
    """
    UPDATE reading_projections AS projection
    SET config_hash = COALESCE(
        snapshot.result_payload ->> 'config_hash',
        snapshot.result_payload -> 'provenance' ->> 'config_hash'
    )
    FROM reading_revisions AS revision,
         reading_plans AS plan,
         chart_snapshots AS snapshot
    WHERE revision.id = COALESCE(
              projection.active_revision_id,
              projection.available_revision_id
          )
      AND revision.guest_id = projection.guest_id
      AND revision.profile_id = projection.profile_id
      AND plan.id = revision.plan_id
      AND plan.guest_id = projection.guest_id
      AND plan.profile_id = projection.profile_id
      AND snapshot.id = plan.chart_snapshot_id
      AND snapshot.guest_id = projection.guest_id
      AND snapshot.profile_id = projection.profile_id
      AND snapshot.result_payload IS NOT NULL
      AND char_length(COALESCE(
              snapshot.result_payload ->> 'config_hash',
              snapshot.result_payload -> 'provenance' ->> 'config_hash'
          )) BETWEEN 1 AND 64
    """
)

_ASSERT_SAFE_BACKFILL = sa.text(
    """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM reading_projections
            WHERE config_hash IS NULL
        ) THEN
            RAISE EXCEPTION USING MESSAGE =
                'No-Go: reading projection config_hash cannot be derived safely; run the '
                'key-aware projection backfill before migration 20260907_0013';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM reading_projections AS projection
            JOIN reading_revisions AS revision
              ON revision.id IN (
                  projection.active_revision_id,
                  projection.available_revision_id
              )
             AND revision.guest_id = projection.guest_id
             AND revision.profile_id = projection.profile_id
            JOIN reading_plans AS plan
              ON plan.id = revision.plan_id
             AND plan.guest_id = projection.guest_id
             AND plan.profile_id = projection.profile_id
            LEFT JOIN chart_snapshots AS snapshot
              ON snapshot.id = plan.chart_snapshot_id
             AND snapshot.guest_id = projection.guest_id
             AND snapshot.profile_id = projection.profile_id
            WHERE COALESCE(
                      snapshot.result_payload ->> 'config_hash',
                      snapshot.result_payload -> 'provenance' ->> 'config_hash'
                  ) IS DISTINCT FROM projection.config_hash
        ) THEN
            RAISE EXCEPTION USING MESSAGE =
                'No-Go: a reading projection pointer has an encrypted, missing, or '
                'different config; decrypt/split it with the key-aware backfill before '
                'migration 20260907_0013';
        END IF;
    END
    $$
    """
)

_REKEY_PROJECTIONS = sa.text(
    r"""
    UPDATE reading_projections AS projection
    SET scope_key = encode(
        sha256(
            convert_to(
                concat_ws(
                    chr(31),
                    projection.purpose,
                    projection.tradition,
                    projection.config_hash,
                    projection.local_date::text,
                    projection.timezone_name,
                    to_char(
                        projection.observed_at AT TIME ZONE 'UTC',
                        'YYYY-MM-DD"T"HH24:MI:SS'
                    ) ||
                    CASE
                        WHEN extract(microseconds FROM projection.observed_at)::integer
                             % 1000000 = 0
                        THEN ''
                        ELSE '.' || to_char(
                            projection.observed_at AT TIME ZONE 'UTC',
                            'US'
                        )
                    END || '+00:00'
                ),
                'UTF8'
            )
        ),
        'hex'
    )
    """
)

_REKEY_GENERATION_ATTEMPTS = sa.text(
    """
    UPDATE reading_generation_attempts AS attempt
    SET generation_key = encode(
        sha256(
            convert_to(
                concat_ws(
                    chr(31),
                    plan.plan_key,
                    attempt.scope_key,
                    attempt.provider,
                    attempt.model,
                    attempt.prompt_version
                ),
                'UTF8'
            )
        ),
        'hex'
    )
    FROM reading_plans AS plan
    WHERE plan.id = attempt.plan_id
      AND plan.guest_id = attempt.guest_id
      AND plan.profile_id = attempt.profile_id
    """
)

_ASSERT_EMPTY_FOR_DOWNGRADE = sa.text(
    """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM reading_projections) THEN
            RAISE EXCEPTION USING MESSAGE =
                'No-Go: purge reading projections or run a key-aware legacy scope-key '
                'backfill before downgrading 20260907_0013';
        END IF;
    END
    $$
    """
)


def upgrade() -> None:
    op.add_column(
        "reading_projections",
        sa.Column("config_hash", sa.String(length=64), nullable=True),
    )
    op.execute(_BACKFILL_CONFIG_HASH)
    op.execute(_ASSERT_SAFE_BACKFILL)
    op.drop_constraint(
        "fk_reading_generation_attempts_projection_owner",
        "reading_generation_attempts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_reading_generation_attempts_projection_owner",
        "reading_generation_attempts",
        "reading_projections",
        ["guest_id", "profile_id", "scope_key"],
        ["guest_id", "profile_id", "scope_key"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.execute(_REKEY_PROJECTIONS)
    # The FK cascades the new scope key; refresh the identity derived from that key too.
    op.execute(_REKEY_GENERATION_ATTEMPTS)
    op.alter_column(
        "reading_projections",
        "config_hash",
        existing_type=sa.String(length=64),
        nullable=False,
    )


def downgrade() -> None:
    # Old application versions cannot validate configuration-aware scope keys.
    op.execute(_ASSERT_EMPTY_FOR_DOWNGRADE)
    op.drop_constraint(
        "fk_reading_generation_attempts_projection_owner",
        "reading_generation_attempts",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_reading_generation_attempts_projection_owner",
        "reading_generation_attempts",
        "reading_projections",
        ["guest_id", "profile_id", "scope_key"],
        ["guest_id", "profile_id", "scope_key"],
        ondelete="CASCADE",
    )
    op.drop_column("reading_projections", "config_hash")
