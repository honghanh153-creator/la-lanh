from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, LargeBinary, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class PrincipalRow(Base):
    __tablename__ = "principals"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_guest_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "guest_sessions.id",
            name="fk_principals_source_guest",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class OwnerSessionRow(Base):
    __tablename__ = "owner_sessions"
    __table_args__ = (Index("ix_owner_sessions_token_hash", "token_hash", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
