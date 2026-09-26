class ResonanceDomainError(Exception):
    code = "RESONANCE_ERROR"
    status_code = 400


class ResonanceTargetNotFound(ResonanceDomainError):
    code = "RESONANCE_TARGET_NOT_FOUND"
    status_code = 404
