"""Keep backend records off Supabase's browser Data API.

Revision ID: 20261008_0028
Revises: 20261004_0027
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261008_0028"
down_revision: str | None = "20261004_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Authorization lives in the backend. No FORCE: its owning role keeps working.
PRIVATE_TABLES = (
    "alembic_version",
    "guest_sessions",
    "consents",
    "guest_session_creations",
    "birth_profiles",
    "mood_check_ins",
    "chart_snapshots",
    "principals",
    "owner_sessions",
    "la_chung_responses",
    "la_chung_reports",
    "reading_plans",
    "reading_revisions",
    "reading_generation_attempts",
    "daily_notes",
    "saved_notes",
    "share_artifacts",
    "la_chung_requests",
    "resonance_feedback",
    "daily_experiments",
    "reading_projections",
    "matching_profiles",
    "matching_consents",
    "content_revisions",
    "matching_verifications",
    "radar_requests",
    "tarot_sessions",
    "content_channels",
    "content_audit_events",
    "content_rewrite_jobs",
)


def protection_sql() -> str:
    tables = ", ".join(f"'{name}'" for name in PRIVATE_TABLES)
    return """
    DO $protect$
    DECLARE table_name text; browser_role text;
    BEGIN
      FOREACH table_name IN ARRAY ARRAY[__PRIVATE_TABLES__] LOOP
        IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
          EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
          EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC', table_name);
          FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
              EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', table_name, browser_role);
            END IF;
          END LOOP;
        END IF;
      END LOOP;
      ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC;
      FOREACH browser_role IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = browser_role) THEN
          EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I',
            browser_role);
        END IF;
      END LOOP;
    END $protect$;
    """.replace("__PRIVATE_TABLES__", tables)


def upgrade() -> None:
    op.execute(protection_sql())


def downgrade() -> None:
    # A code rollback must not restore browser access to private records.
    pass
