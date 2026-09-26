class SavedDomainError(Exception):
    code = "SAVED_NOTE_ERROR"
    status_code = 400


class SavedRevisionUnavailable(SavedDomainError):
    """The requested reading is stale, absent, or outside the guest's active scope."""

    code = "SAVED_REVISION_UNAVAILABLE"
    status_code = 404


class SavedReadingUnavailable(SavedDomainError):
    code = "SAVED_READING_UNAVAILABLE"
    status_code = 503
