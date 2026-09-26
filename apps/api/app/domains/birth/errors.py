class BirthDomainError(Exception):
    code = "BIRTH_ERROR"
    status_code = 400


class BirthDateOutOfRange(BirthDomainError):
    code = "BIRTH_DATE_OUT_OF_RANGE"
    status_code = 422


class BirthProfileNotFound(BirthDomainError):
    code = "BIRTH_PROFILE_NOT_FOUND"
    status_code = 404


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
