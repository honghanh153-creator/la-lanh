class GuestDomainError(Exception):
    code = "GUEST_ERROR"
    status_code = 400


class ConsentVersionInvalid(GuestDomainError):
    code = "CONSENT_VERSION_INVALID"
    status_code = 422


class ConsentPurposeInvalid(GuestDomainError):
    code = "CONSENT_PURPOSE_INVALID"
    status_code = 422


class IdempotencyKeyInvalid(GuestDomainError):
    code = "IDEMPOTENCY_KEY_INVALID"
    status_code = 422


class IdempotencyConflict(GuestDomainError):
    code = "IDEMPOTENCY_CONFLICT"
    status_code = 409


class IdempotencyReplayExpired(GuestDomainError):
    code = "IDEMPOTENCY_REPLAY_EXPIRED"
    status_code = 409


class GuestSessionMissing(GuestDomainError):
    code = "GUEST_SESSION_MISSING"
    status_code = 401


class GuestExpired(GuestDomainError):
    code = "GUEST_EXPIRED"
    status_code = 401


class GuestNotFound(GuestDomainError):
    code = "GUEST_NOT_FOUND"
    status_code = 404


class CsrfRejected(GuestDomainError):
    code = "CSRF_REJECTED"
    status_code = 403
