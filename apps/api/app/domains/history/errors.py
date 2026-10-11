from app.domains.birth.errors import BirthProfileNotFound
from app.domains.guest.errors import GuestDomainError


class HistoryUnavailable(BirthProfileNotFound):
    code = "HISTORY_UNAVAILABLE"


class HistoryBusy(GuestDomainError):
    code = "HISTORY_BUSY"
    status_code = 409
