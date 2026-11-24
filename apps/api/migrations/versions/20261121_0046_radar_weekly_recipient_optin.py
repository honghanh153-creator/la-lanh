"""Hợp gu "Hai bạn tuần này": the invited person keeps the pair (owner AR1, 21.11.2026).

Revision ID: 20261121_0046
Revises: 20261120_0045

A pair is kept only when the invited person ticks their own box on the link page. Two columns
let that person delete it again for its whole 90 days:

- ``request_id``: the result the pair came from, so withdrawing the result deletes the pair
  (no foreign key: the pair outlives the 30-day result);
- ``invite_token_hash``: the same HMAC as the invite's ``token_hash``, so the invite link can
  still delete the pair after the result is gone.

No raw token and no new personal data; both columns are nullable and start empty.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261121_0046"
down_revision: str | Sequence[str] | None = "20261120_0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("radar_weekly_pairs", sa.Column("request_id", sa.Uuid(), nullable=True))
    op.add_column(
        "radar_weekly_pairs", sa.Column("invite_token_hash", sa.LargeBinary(32), nullable=True)
    )
    op.create_index("ix_radar_weekly_request", "radar_weekly_pairs", ["request_id"])
    op.create_index("ix_radar_weekly_invite_token", "radar_weekly_pairs", ["invite_token_hash"])


def downgrade() -> None:
    op.drop_index("ix_radar_weekly_invite_token", table_name="radar_weekly_pairs")
    op.drop_index("ix_radar_weekly_request", table_name="radar_weekly_pairs")
    op.drop_column("radar_weekly_pairs", "invite_token_hash")
    op.drop_column("radar_weekly_pairs", "request_id")
