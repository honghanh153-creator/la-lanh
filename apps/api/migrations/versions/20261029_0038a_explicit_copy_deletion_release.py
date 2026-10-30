"""Compatibility release marker: the app now deletes saved and shared copies explicitly (US-23).

No schema change. From this release on, every path that must remove saved notes and share links
with their source (birth time/place removal, manual history clear) deletes them in application
code, while the source cascades still stand. The next release's migration 20261029_0039 drops
those cascades; it revises this marker and refuses to run in the same upgrade that applies it, so
an app that relies on the cascades is never left running on the schema without them (Codex r56).

Release order: deploy this release and let it replace every app process first; only then deploy
the release carrying 20261029_0039. Once 20261029_0039 is applied, roll back only to an image of
this release or later.

Revision ID: 20261029_0038a
Revises: 20261023_0038
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261029_0038a"
down_revision: str | Sequence[str] | None = "20261023_0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Set on the migration connection when this marker is applied, so 20261029_0039 can tell that the
# compatibility release is being applied in the same run instead of an earlier one.
APPLIED_THIS_RUN = "la_lanh_explicit_copy_deletion_applied_this_run"


def upgrade() -> None:
    if not op.get_context().as_sql:
        op.get_bind().info[APPLIED_THIS_RUN] = True


def downgrade() -> None:
    # Nothing to undo: the cascades this release relies on still stand.
    pass
