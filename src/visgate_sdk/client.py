"""visgate API client (sync and async)."""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from visgate_sdk.exceptions import (
    AuthenticationError,
    ConnectionError,
    ProviderError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    VisgateError,
)

logger = logging.getLogger("visgate_sdk")

DEFAULT_BASE_URL = "https://visgateai.com/api/v1"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 2

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("visgate-sdk")
    except Exception:
        return "0.0.0-dev"


_VERSION = _get_version()


def _resolve_api_key(api_key: Optional[str]) -> str:
    """Resolve API key from argument or environment variable."""
    key = api_key or os.environ.get("VISGATE_API_KEY")
    if not key:
        raise AuthenticationError(
            "No API key provided. Pass api_key= or set the VISGATE_API_KEY environment variable."
        )
    return key


def _build_headers(
    api_key: str,
    *,
    fal_key: Optional[str] = None,
    replicate_key: Optional[str] = None,
    runway_key: Optional[str] = None,
) -> Dict[str, str]:
    """Build default request headers."""
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": f"visgate-sdk-python/{_VERSION}",
    }
    if fal_key:
        headers["X-Fal-Key"] = fal_key
    if replicate_key:
        headers["X-Replicate-Key"] = replicate_key
    if runway_key:
        headers["X-Runway-Key"] = runway_key
    return headers


def _handle_response(response: httpx.Response) -> Any:
    """Parse API response. Raises typed exceptions on error."""
    status = response.status_code

    if status < 400:
        return response.json()

    if status == 401:
        raise AuthenticationError("Invalid or missing API key")

    if status == 422:
        try:
            data = response.json()
            message = data.get("message", response.text)
            field = data.get("details", {}).get("field")
        except Exception:
            message = response.text
            field = None
        raise ValidationError(message, field=field)

    if status == 429:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(
            "Rate limit exceeded",
            retry_after=int(retry_after) if retry_after else None,
        )

    # All other errors
    try:
        data = response.json()
        error_code = data.get("error", "UNKNOWN_ERROR")
        message = data.get("message", response.text)
    except Exception:
        error_code = f"HTTP_{status}"
        message = response.text
        data = {}

    if "PROVIDER" in error_code:
        provider = data.get("details", {}).get("provider", "unknown")
        raise ProviderError(message, provider=provider)

    raise VisgateError(message, error_code=error_code, status_code=status)


class Client:
    """Synchronous visgate API client.

    Args:
        api_key: visgate API key (``vg-...``). If not provided, reads from
            the ``VISGATE_API_KEY`` environment variable.
        base_url: API base URL. Defaults to ``https://visgateai.com/api/v1``.
        timeout: Request timeout in seconds. Defaults to 120.
        max_retries: Number of automatic retries for transient errors (429, 5xx).
            Defaults to 2. Set to 0 to disable.
        fal_key: Optional Fal.ai API key for BYOK mode.
        replicate_key: Optional Replicate API key for BYOK mode.
        runway_key: Optional Runway API key for BYOK mode.

    Usage::

        from visgate_sdk import Client

        client = Client()  # reads VISGATE_API_KEY from env
        result = client.generate("a sunset over mountains")
        print(result.image_url)
        client.close()

    Or as a context manager::

        with Client() as client:
            models = client.models.list(limit=10)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        fal_key: Optional[str] = None,
        replicate_key: Optional[str] = None,
        runway_key: Optional[str] = None,
    ):
        self.api_key = _resolve_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._fal_key = fal_key
        self._replicate_key = replicate_key
        self._runway_key = runway_key

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=_build_headers(
                self.api_key,
                fal_key=fal_key,
                replicate_key=replicate_key,
                runway_key=runway_key,
            ),
        )

        # Resources
        from visgate_sdk.resources.generate import Generate
        from visgate_sdk.resources.images import Images
        from visgate_sdk.resources.models import Models
        from visgate_sdk.resources.providers import Providers
        from visgate_sdk.resources.requests import Requests
        from visgate_sdk.resources.usage import Usage
        from visgate_sdk.resources.videos import Videos

        self.images = Images(self)
        self.models = Models(self)
        self.videos = Videos(self)
        self.requests = Requests(self)
        self.usage = Usage(self)
        self.providers = Providers(self)
        self._generate = Generate(self)

    def generate(
        self,
        prompt: str,
        model: str = "fal-ai/flux/schnell",
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Generate an image with a single call.

        Args:
            prompt: Text description of the image to generate.
            model: Model identifier. Defaults to ``fal-ai/flux/schnell``.
            params: Optional model-specific parameters.

        Returns:
            GenerateResult with ``image_url``, ``images``, ``cost``, ``provider``, etc.
        """
        return self._generate(prompt=prompt, model=model, params=params)

    def set_provider_headers(
        self,
        *,
        fal_key: Optional[str] = None,
        replicate_key: Optional[str] = None,
        runway_key: Optional[str] = None,
    ) -> None:
        """Update BYOK provider keys for subsequent requests.

        Omitted keys are set to None (managed mode). Pass a key to use BYOK for that provider.
        """
        self._fal_key = fal_key or None
        self._replicate_key = replicate_key or None
        self._runway_key = runway_key or None
        # Rebuild the underlying httpx client with new headers
        self._client.close()
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            headers=_build_headers(
                self.api_key,
                fal_key=self._fal_key,
                replicate_key=self._replicate_key,
                runway_key=self._runway_key,
            ),
        )

    def health(self) -> Dict[str, Any]:
        """Check API health status.

        Returns:
            Dict with ``status``, ``version``, ``database``, ``cache`` keys.
        """
        return self._request("GET", "/health")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send an HTTP request with automatic retry on transient errors."""
        last_exc: Optional[Exception] = None

        for attempt in range(1 + self.max_retries):
            try:
                logger.debug("%s %s (attempt %d)", method, path, attempt + 1)
                response = self._client.request(method, path, **kwargs)

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    wait = _retry_wait(response, attempt)
                    logger.info("Retryable %d, waiting %.1fs", response.status_code, wait)
                    time.sleep(wait)
                    continue

                return _handle_response(response)

            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = _backoff(attempt)
                    logger.info("Timeout, retrying in %.1fs", wait)
                    time.sleep(wait)
                    continue
                raise TimeoutError(f"Request timed out after {attempt + 1} attempt(s)") from exc

            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = _backoff(attempt)
                    logger.info("Connection error, retrying in %.1fs", wait)
                    time.sleep(wait)
                    continue
                raise ConnectionError(f"Connection failed: {exc}") from exc

        # Should not reach here, but just in case
        raise VisgateError(f"Request failed after {self.max_retries + 1} attempts") from last_exc

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Client(base_url={self.base_url!r})"


class AsyncClient:
    """Asynchronous visgate API client.

    Accepts the same arguments as :class:`Client`. Use ``async with`` for
    automatic cleanup::

        async with AsyncClient() as client:
            models = await client.models.list(limit=10)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        fal_key: Optional[str] = None,
        replicate_key: Optional[str] = None,
        runway_key: Optional[str] = None,
    ):
        self.api_key = _resolve_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=_build_headers(
                self.api_key,
                fal_key=fal_key,
                replicate_key=replicate_key,
                runway_key=runway_key,
            ),
        )

        # Resources
        from visgate_sdk.resources.generate import AsyncGenerate
        from visgate_sdk.resources.images import AsyncImages
        from visgate_sdk.resources.models import AsyncModels
        from visgate_sdk.resources.providers import AsyncProviders
        from visgate_sdk.resources.requests import AsyncRequests
        from visgate_sdk.resources.usage import AsyncUsage
        from visgate_sdk.resources.videos import AsyncVideos

        self.images = AsyncImages(self)
        self.models = AsyncModels(self)
        self.videos = AsyncVideos(self)
        self.requests = AsyncRequests(self)
        self.usage = AsyncUsage(self)
        self.providers = AsyncProviders(self)
        self._generate = AsyncGenerate(self)

    async def generate(
        self,
        prompt: str,
        model: str = "fal-ai/flux/schnell",
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Generate an image (async). See :meth:`Client.generate` for details."""
        return await self._generate(prompt=prompt, model=model, params=params)

    async def health(self) -> Dict[str, Any]:
        """Check API health status (async)."""
        return await self._request("GET", "/health")

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send an HTTP request with automatic retry on transient errors."""
        import asyncio

        last_exc: Optional[Exception] = None

        for attempt in range(1 + self.max_retries):
            try:
                logger.debug("%s %s (attempt %d)", method, path, attempt + 1)
                response = await self._client.request(method, path, **kwargs)

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    wait = _retry_wait(response, attempt)
                    logger.info("Retryable %d, waiting %.1fs", response.status_code, wait)
                    await asyncio.sleep(wait)
                    continue

                return _handle_response(response)

            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = _backoff(attempt)
                    logger.info("Timeout, retrying in %.1fs", wait)
                    await asyncio.sleep(wait)
                    continue
                raise TimeoutError(f"Request timed out after {attempt + 1} attempt(s)") from exc

            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = _backoff(attempt)
                    logger.info("Connection error, retrying in %.1fs", wait)
                    await asyncio.sleep(wait)
                    continue
                raise ConnectionError(f"Connection failed: {exc}") from exc

        raise VisgateError(f"Request failed after {self.max_retries + 1} attempts") from last_exc

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"AsyncClient(base_url={self.base_url!r})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _backoff(attempt: int) -> float:
    """Exponential backoff: 0.5s, 1s, 2s, ..."""
    return min(0.5 * (2**attempt), 8.0)


def _retry_wait(response: httpx.Response, attempt: int) -> float:
    """Use Retry-After header if present, otherwise exponential backoff."""
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return _backoff(attempt)
