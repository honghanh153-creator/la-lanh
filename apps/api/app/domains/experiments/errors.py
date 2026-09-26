class ExperimentDomainError(Exception):
    code = "EXPERIMENT_ERROR"
    status_code = 400


class ExperimentTargetNotFound(ExperimentDomainError):
    code = "EXPERIMENT_TARGET_NOT_FOUND"
    status_code = 404


class ExperimentReplaceRequired(ExperimentDomainError):
    code = "EXPERIMENT_REPLACE_REQUIRED"
    status_code = 409


class ExperimentConflict(ExperimentDomainError):
    code = "EXPERIMENT_CONFLICT"
    status_code = 409
