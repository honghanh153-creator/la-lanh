"""Pin append-only trigger name resolution; no data or trigger behavior change."""

from alembic import op

revision = "20261010_0035"
down_revision = "20261010_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for function in ("guard_content_revision_history", "guard_content_audit_history"):
            op.execute(f"ALTER FUNCTION public.{function}() SET search_path = pg_catalog")


def downgrade() -> None:
    # Additive safety posture remains valid for the previous application image.
    pass
