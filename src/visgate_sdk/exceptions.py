"""visgate SDK exceptions. All extend VisgateError."""
from __future__ import annotations

from typing import Any, Dict, Optional


class VisgateError(Exception):
    """Base exception for all visgate SDK errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code (e.g. ``"AUTHENTICATION_ERROR"``).
        details: Additional structured error context.
        status_code: HTTP status code that triggered this error, if any.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "VISGATE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message={self.message!r}, error_code={self.error_code!r})"


class AuthenticationError(VisgateError):
    """401 -- invalid or missing API key."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, "AUTHENTICATION_ERROR", status_code=401)


class ValidationError(VisgateError):
    """422 -- invalid request parameters.

    Attributes:
        field: The specific field that failed validation, if available.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        details = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details, status_code=422)


class RateLimitError(VisgateError):
    """429 -- too many requests.

    Attributes:
        retry_after: Seconds to wait before retrying, if the server provided it.
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, "RATE_LIMIT_ERROR", details, status_code=429)


class ProviderError(VisgateError):
    """Upstream provider error (e.g. Fal, Replicate, Runway).

    Attributes:
        provider: Name of the provider that failed.
    """

    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(message, "PROVIDER_ERROR", {"provider": provider})


class TimeoutError(VisgateError):
    """Request timed out before the server responded."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, "TIMEOUT_ERROR")


class ConnectionError(VisgateError):
    """Network connection failed."""

    def __init__(self, message: str = "Connection failed"):
        super().__init__(message, "CONNECTION_ERROR")
