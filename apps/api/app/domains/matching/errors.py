class MatchingDomainError(RuntimeError):
    status_code = 400
    code = "MATCHING_REQUEST_REJECTED"


class MatchingProfileRequired(MatchingDomainError):
    status_code = 409
    code = "MATCHING_PROFILE_REQUIRED"


class MatchingConsentInvalid(MatchingDomainError):
    status_code = 422
    code = "MATCHING_CONSENT_INVALID"


class MatchingProfileInvalid(MatchingDomainError):
    status_code = 422
    code = "MATCHING_PROFILE_INVALID"


class MatchingNotReady(MatchingDomainError):
    status_code = 409
    code = "MATCHING_NOT_READY"
