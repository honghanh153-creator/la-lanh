from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class SavedNoteRow(Base):
    __tablename__ = "saved_notes"
    # A saved note is a frozen copy the person chose to keep (US-23 D2). Since migration
    # 20261029_0039 it no longer cascades from its Daily note or reading revision: the ids stay as
    # plain identifiers for unsave and queued unsaves, and every source-deleting path that must
    # also remove copies deletes them explicitly. Guest deletion still cascades through guest_id.
    __table_args__ = (
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
    daily_note_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
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
