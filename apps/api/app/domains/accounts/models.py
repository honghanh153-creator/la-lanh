from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

from app.domains.guest.models import GuestSessionRecord

ACCOUNT_DAYS = 365
DEVICE_DAYS = 30
CHALLENGE_SECONDS = 600
STORAGE_CONSENT = "account-storage-v1"


class AccountError(Exception):
    def __init__(self, code: str, status: int = 400, *, retry_after: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class ProviderIdentity:
    subject: UUID
    masked_email: str


@dataclass(frozen=True)
class AccountDevice:
    id: UUID
    current: bool
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class Challenge:
    cookie: str = field(repr=False)
    csrf_token: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True)
class LoginResult:
    status: Literal["signed_in", "restore_required", "onboarding_required", "consent_required"]
    guest: GuestSessionRecord | None = None
    token: str | None = field(default=None, repr=False)
    csrf_token: str | None = field(default=None, repr=False)
    restore_token: str | None = field(default=None, repr=False)
    masked_email: str | None = None
    profile_expires_at: datetime | None = None
