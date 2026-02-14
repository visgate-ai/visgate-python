"""Async generation request status: ``GET /requests/{id}`` with optional polling."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from visgate_sdk.client import AsyncClient, Client


@dataclass
class RequestStatusResult:
    """Status of an async generation request.

    Attributes:
        request_id: Unique request identifier.
        status: One of ``pending``, ``processing``, ``completed``, ``failed``.
        media_type: One of ``image``, ``video``, ``audio``.
        provider: Provider name.
        model: Model identifier.
        output_url: URL of the generated media when status is ``completed``.
        error_message: Error details when status is ``failed``.
        created_at: ISO timestamp when request was created.
        completed_at: ISO timestamp when request completed (success or failure).
    """

    request_id: str
    status: str
    media_type: str
    provider: str
    model: str
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RequestStatusResult:
        return cls(
            request_id=data.get("request_id", data.get("id", "")),
            status=data.get("status", "pending"),
            media_type=data.get("media_type", "video"),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            output_url=data.get("output_url"),
            error_message=data.get("error_message"),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
        )

    @property
    def is_terminal(self) -> bool:
        """True when status is completed or failed."""
        return self.status in ("completed", "failed")

    def __repr__(self) -> str:
        return f"RequestStatusResult(request_id={self.request_id!r}, status={self.status!r})"


class GenerationRequest:
    """Response from async generation (202) with sync client. Use :meth:`wait` to poll."""

    def __init__(self, request_id: str, client: "Client") -> None:
        self.request_id = request_id
        self.status = "pending"
        self._client = client

    def wait(
        self,
        *,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> RequestStatusResult:
        """Poll until completed or failed. Returns final RequestStatusResult."""
        return self._client.requests.get(
            self.request_id,
            wait=True,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    def __repr__(self) -> str:
        return f"GenerationRequest(request_id={self.request_id!r})"


class AsyncGenerationRequest:
    """Response from async generation (202) with async client. Use :meth:`wait` to poll."""

    def __init__(self, request_id: str, client: "AsyncClient") -> None:
        self.request_id = request_id
        self.status = "pending"
        self._client = client

    async def wait(
        self,
        *,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> RequestStatusResult:
        """Poll until completed or failed. Returns final RequestStatusResult."""
        return await self._client.requests.get(
            self.request_id,
            wait=True,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    def __repr__(self) -> str:
        return f"AsyncGenerationRequest(request_id={self.request_id!r})"


class Requests:
    """Async generation request status (sync)."""

    def __init__(self, client: "Client") -> None:
        self._client = client

    def get(
        self,
        request_id: str,
        *,
        wait: bool = False,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> RequestStatusResult:
        """Get status of an async generation request.

        Args:
            request_id: Request ID from 202 response.
            wait: If True, poll until completed or failed (or timeout).
            timeout: Max seconds to wait when wait=True. Defaults to 300.
            poll_interval: Seconds between polls when wait=True. Defaults to 2.

        Returns:
            RequestStatusResult with status, output_url when completed, or error_message when failed.
        """
        start = time.perf_counter()
        while True:
            data = self._client._request("GET", f"/requests/{request_id}")
            result = RequestStatusResult.from_dict(data)
            if not wait or result.is_terminal:
                return result
            elapsed = time.perf_counter() - start
            if elapsed >= timeout:
                return result
            time.sleep(min(poll_interval, max(0.1, timeout - elapsed)))


class AsyncRequests:
    """Async generation request status (async)."""

    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def get(
        self,
        request_id: str,
        *,
        wait: bool = False,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> RequestStatusResult:
        """Get status of an async generation request. See :meth:`Requests.get` for details."""
        import asyncio

        start = time.perf_counter()
        while True:
            data = await self._client._request("GET", f"/requests/{request_id}")
            result = RequestStatusResult.from_dict(data)
            if not wait or result.is_terminal:
                return result
            elapsed = time.perf_counter() - start
            if elapsed >= timeout:
                return result
            await asyncio.sleep(min(poll_interval, max(0.1, timeout - elapsed)))
