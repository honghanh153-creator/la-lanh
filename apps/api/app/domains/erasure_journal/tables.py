from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class ErasureJournalRow(Base):
    """A pseudonymous fact that a person erased or withdrew something (audit P07, option A).

    Only a keyed digest of the root id, the kind of action and its time; never content. It lets a
    restore replay explicit user erasures made after the backup (see erasure_journal.replay).
    """

    __tablename__ = "erasure_journal"
    __table_args__ = (
        UniqueConstraint("kind", "subject_digest", "scope", "occurred_at", name="uq_erasure_entry"),
        Index("ix_erasure_journal_occurred", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    # A closed qualifier (consent purpose, removed supplement fields); "" when none.
    scope: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
