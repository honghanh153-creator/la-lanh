from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Index, LargeBinary, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UtcDateTime


class BirthProfileRow(Base):
    __tablename__ = "birth_profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "chart_snapshots.id",
            name="fk_birth_profiles_current_snapshot",
            use_alter=True,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

    snapshots: Mapped[list["ChartSnapshotRow"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ChartSnapshotRow.profile_id",
    )


class ChartSnapshotRow(Base):
    __tablename__ = "chart_snapshots"
    __table_args__ = (
        Index("ix_chart_snapshots_guest_created", "guest_id", "created_at"),
        Index("ux_chart_snapshots_guest_input", "guest_id", "input_hash", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("birth_profiles.id", ondelete="CASCADE"), nullable=False
    )
    input_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    birth_date_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    calculation_profile: Mapped[str] = mapped_column(String(64), nullable=False)
    result_payload: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)

    profile: Mapped[BirthProfileRow] = relationship(
        back_populates="snapshots", foreign_keys=[profile_id]
    )
