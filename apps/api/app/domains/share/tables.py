from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class ShareArtifactRow(Base):
    """A frozen, privacy-safe copy behind a public link.

    Since migration 20261029_0039 it no longer cascades from its Daily note or reading revision
    (US-23 D2): a birth-date correction keeps live links listable and revocable. Paths that must
    remove links with their source delete them explicitly; guest deletion still cascades.
    """

    __tablename__ = "share_artifacts"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_share_artifact_expiry_after_creation"),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="ck_share_artifact_revocation_after_creation",
        ),
        CheckConstraint(
            "(revision_id IS NULL AND profile_id IS NULL) OR "
            "(revision_id IS NOT NULL AND profile_id IS NOT NULL)",
            name="ck_share_artifacts_revision_bundle",
        ),
        Index("ix_share_artifacts_token_hash", "token_hash", unique=True),
        Index("ix_share_artifacts_guest_created", "guest_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    daily_note_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    revision_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    safe_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    safe_snapshot_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
