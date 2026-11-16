"""Application errors. Each carries an HTTP status code and a machine-readable code.

main.py turns any AppError into a JSON response: {"detail": "...", "code": "..."}.
Services raise these; they never import FastAPI, so they are easy to test.
"""

from typing import Optional


class AppError(Exception):
    status_code = 500
    default_code = "app_error"

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code


class BadRequestError(AppError):
    status_code = 400
    default_code = "bad_request"


class NotFoundError(AppError):
    status_code = 404
    default_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    default_code = "conflict"


class PayloadTooLargeError(AppError):
    status_code = 413
    default_code = "payload_too_large"


class UnsupportedMediaTypeError(AppError):
    status_code = 415
    default_code = "unsupported_media_type"


class RateLimitedError(AppError):
    status_code = 429
    default_code = "ai_rate_limited"


class UpstreamError(AppError):
    """The AI provider failed or returned something unusable."""

    status_code = 502
    default_code = "ai_upstream_error"


class ServiceUnavailableError(AppError):
    """The AI feature is not configured or the provider can't be reached."""

    status_code = 503
    default_code = "ai_unavailable"
