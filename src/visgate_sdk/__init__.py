"""visgate Python SDK — unified client for the visgate vision ai gateway."""
from __future__ import annotations

from visgate_sdk.client import AsyncClient, Client
from visgate_sdk.exceptions import (
    AuthenticationError,
    ConnectionError,
    ProviderError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    VisgateError,
)
from visgate_sdk.resources.generate import GenerateResult
from visgate_sdk.resources.images import ImageResult
from visgate_sdk.resources.models import FeaturedSection, ModelInfo, ModelsResponse
from visgate_sdk.resources.providers import (
    ProviderBalanceItem,
    ProviderBalancesResponse,
    ProviderKeyInfo,
    ProviderKeysResponse,
    ProviderValidationResult,
)
from visgate_sdk.resources.requests import RequestStatusResult
from visgate_sdk.resources.usage import UsageSummary
from visgate_sdk.resources.videos import VideoResult

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("visgate-sdk")
except Exception:
    __version__ = "0.0.0-dev"

__all__ = [
    # Clients
    "Client",
    "AsyncClient",
    # Result types
    "GenerateResult",
    "ImageResult",
    "VideoResult",
    "ModelInfo",
    "ModelsResponse",
    "FeaturedSection",
    "UsageSummary",
    "RequestStatusResult",
    # Provider types
    "ProviderBalanceItem",
    "ProviderBalancesResponse",
    "ProviderKeyInfo",
    "ProviderKeysResponse",
    "ProviderValidationResult",
    # Exceptions
    "VisgateError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "ProviderError",
    "TimeoutError",
    "ConnectionError",
    # Meta
    "__version__",
]
