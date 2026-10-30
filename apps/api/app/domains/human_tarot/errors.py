class HumanTarotError(Exception):
    code = "HUMAN_TAROT_ERROR"
    status_code = 400


class HumanTarotDisabled(HumanTarotError):
    code = "HUMAN_TAROT_DISABLED"
    status_code = 404


class HumanTarotNotFound(HumanTarotError):
    code = "HUMAN_TAROT_NOT_FOUND"
    status_code = 404


class HumanTarotConsentRequired(HumanTarotError):
    code = "HUMAN_TAROT_CONSENT_REQUIRED"
    status_code = 422


class HumanTarotKeyInvalid(HumanTarotError):
    code = "HUMAN_TAROT_KEY_INVALID"
    status_code = 422


class HumanTarotConflict(HumanTarotError):
    code = "HUMAN_TAROT_CONFLICT"
    status_code = 409


class HumanTarotClosed(HumanTarotError):
    code = "HUMAN_TAROT_CLOSED"
    status_code = 409


class HumanTarotFull(HumanTarotError):
    code = "HUMAN_TAROT_FULL"
    status_code = 409


class HumanTarotAlreadyRequested(HumanTarotError):
    code = "HUMAN_TAROT_ALREADY_REQUESTED"
    status_code = 409
