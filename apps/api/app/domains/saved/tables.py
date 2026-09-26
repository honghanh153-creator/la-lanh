from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class SavedNoteRow(Base):
    __tablename__ = "saved_notes"
    __table_args__ = (
        ForeignKeyConstraint(
            ("revision_id", "guest_id", "profile_id"),
            (
                "reading_revisions.id",
                "reading_revisions.guest_id",
                "reading_revisions.profile_id",
            ),
            name="fk_saved_notes_revision_owner",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "(revision_id IS NULL AND profile_id IS NULL AND reading_snapshot IS NULL) OR "
            "(revision_id IS NOT NULL AND profile_id IS NOT NULL AND reading_snapshot IS NOT NULL)",
            name="ck_saved_notes_revision_bundle",
        ),
        Index("ux_saved_notes_guest_note", "guest_id", "daily_note_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    daily_note_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_notes.id", ondelete="CASCADE"), nullable=False
    )
    note_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    snapshot_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    revision_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    reading_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON(none_as_null=True).with_variant(JSONB(none_as_null=True), "postgresql"), nullable=True
    )
    saved_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
