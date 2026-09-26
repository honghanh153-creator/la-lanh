class ShareDomainError(Exception):
    code = "SHARE_ERROR"
    status_code = 400


class ShareArtifactUnavailable(ShareDomainError):
    """The artifact is absent, expired, revoked, or not owned by the caller."""

    code = "SHARE_ARTIFACT_UNAVAILABLE"
    status_code = 404


class ShareReadingUnavailable(ShareDomainError):
    code = "SHARE_READING_UNAVAILABLE"
    status_code = 503
