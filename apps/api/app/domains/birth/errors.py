class BirthDomainError(Exception):
    code = "BIRTH_ERROR"
    status_code = 400


class BirthDateOutOfRange(BirthDomainError):
    code = "BIRTH_DATE_OUT_OF_RANGE"
    status_code = 422


class BirthProfileNotFound(BirthDomainError):
    code = "BIRTH_PROFILE_NOT_FOUND"
    status_code = 404


class BirthProfileChanged(BirthDomainError):
    code = "BIRTH_PROFILE_CHANGED"
    status_code = 409


class ChartEngineUnavailable(BirthDomainError):
    code = "CHART_ENGINE_UNAVAILABLE"
    status_code = 503


class BirthChartBusy(BirthDomainError):
    code = "BIRTH_CHART_BUSY"
    status_code = 429


class BirthSupplementInvalid(BirthDomainError):
    code = "BIRTH_SUPPLEMENT_INVALID"
    status_code = 422


class BirthSupplementConsentInvalid(BirthDomainError):
    code = "BIRTH_SUPPLEMENT_CONSENT_INVALID"
    status_code = 422


class BirthDateUnchanged(BirthDomainError):
    code = "BIRTH_DATE_UNCHANGED"
    status_code = 409


class BirthDateChangeRequiresEdit(BirthDomainError):
    """A different date while an active subject exists: only the explicit edit replaces it."""

    code = "BIRTH_DATE_CHANGE_REQUIRES_EDIT"
    status_code = 409


class BirthDateChangeLimited(BirthDomainError):
    code = "BIRTH_DATE_CHANGE_LIMITED"
    status_code = 429


class BirthDateConfirmationMismatch(BirthDomainError):
    code = "BIRTH_DATE_CONFIRMATION_MISMATCH"
    status_code = 422
