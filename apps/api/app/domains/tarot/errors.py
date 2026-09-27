from app.domains.tarot.models import TarotQuestionAssessment


class TarotDomainError(Exception):
    code = "TAROT_ERROR"
    status_code = 400


class TarotSessionNotFound(TarotDomainError):
    code = "TAROT_SESSION_NOT_FOUND"
    status_code = 404


class TarotSessionConflict(TarotDomainError):
    code = "TAROT_SESSION_CONFLICT"
    status_code = 409


class TarotSelectionInvalid(TarotDomainError):
    code = "TAROT_SELECTION_INVALID"
    status_code = 422


class TarotQuestionRejected(TarotDomainError):
    code = "TAROT_QUESTION_REFRAME_REQUIRED"
    status_code = 422

    def __init__(self, assessment: TarotQuestionAssessment) -> None:
        super().__init__(assessment.explanation)
        self.assessment = assessment
