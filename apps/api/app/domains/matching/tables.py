from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UtcDateTime


class MatchingProfileRow(Base):
    __tablename__ = "matching_profiles"
    __table_args__ = (
        CheckConstraint("min_age >= 18", name="ck_matching_profiles_min_age"),
        CheckConstraint("max_age <= 120", name="ck_matching_profiles_max_age"),
        CheckConstraint("min_age <= max_age", name="ck_matching_profiles_age_range"),
        CheckConstraint(
            "intent IN ('dating', 'friendship', 'open')",
            name="ck_matching_profiles_intent",
        ),
        CheckConstraint(
            "gender_identity IN ('woman', 'man', 'nonbinary')",
            name="ck_matching_profiles_gender_identity",
        ),
        CheckConstraint(
            "gender_preference IN ('women', 'men', 'nonbinary', 'everyone')",
            name="ck_matching_profiles_gender_preference",
        ),
        CheckConstraint(
            "weekly_intent IN ('de_noi_chuyen', 'di_cham', 'goc_moi', 'de_la_can')",
            name="ck_matching_profiles_weekly_intent",
        ),
        Index("ix_matching_profiles_active_region", "active", "region_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    gender_identity: Mapped[str] = mapped_column(String(24), nullable=False)
    intent: Mapped[str] = mapped_column(String(24), nullable=False)
    gender_preference: Mapped[str] = mapped_column(String(24), nullable=False)
    min_age: Mapped[int] = mapped_column(Integer, nullable=False)
    max_age: Mapped[int] = mapped_column(Integer, nullable=False)
    region_code: Mapped[str] = mapped_column(String(64), nullable=False)
    weekly_intent: Mapped[str] = mapped_column(String(24), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


class MatchingConsentRow(Base):
    __tablename__ = "matching_consents"
    __table_args__ = (
        Index(
            "ux_matching_consents_principal_active",
            "principal_id",
            unique=True,
            sqlite_where=text("revoked_at IS NULL"),
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index("ix_matching_consents_active", "principal_id", "revoked_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime())


class MatchingVerificationRow(Base):
    __tablename__ = "matching_verifications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'pending', 'pass', 'fail')",
            name="ck_matching_verifications_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    principal_id: Mapped[UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(64))
    provider_reference: Mapped[str | None] = mapped_column(String(128))
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
