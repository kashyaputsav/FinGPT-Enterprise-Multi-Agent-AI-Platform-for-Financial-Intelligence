"""Domain-level exceptions mapped to HTTP responses in app/main.py."""


class AppException(Exception):
    status_code = 500
    detail = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotAuthenticatedError(AppException):
    status_code = 401
    detail = "Authentication required"


class PermissionDeniedError(AppException):
    status_code = 403
    detail = "You do not have permission to perform this action"


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"


class ValidationFailedError(AppException):
    status_code = 422
    detail = "Validation failed"


class RateLimitExceededError(AppException):
    status_code = 429
    detail = "Rate limit exceeded, please try again later"


class RetrievalError(AppException):
    status_code = 502
    detail = "Failed to retrieve context from knowledge base"


class AgentExecutionError(AppException):
    status_code = 502
    detail = "Agent execution failed"
