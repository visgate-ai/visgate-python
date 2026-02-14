"""Video generation: ``POST /videos/generate``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from visgate_sdk._utils import parse_datetime
from visgate_sdk.resources.requests import AsyncGenerationRequest, GenerationRequest

if TYPE_CHECKING:
    from datetime import datetime

    from visgate_sdk.client import AsyncClient, Client


@dataclass
class VideoResult:
    """Result of a video generation request.

    Attributes:
        id: Unique request identifier.
        video_url: URL of the generated video (may be ``None`` if still processing).
        model: Model identifier used.
        provider: Provider name (e.g. ``"runway"``).
        cost: Cost in USD.
        cache_hit: Whether the result was served from cache.
        provider_cost_avoided_micro: When cache_hit is True, provider cost avoided in micro-USD (1e-6 USD).
        latency_ms: Server-side latency in milliseconds.
        created_at: Timestamp of the request.
    """

    id: str
    video_url: Optional[str]
    model: str
    provider: str
    cost: float
    cache_hit: bool = False
    provider_cost_avoided_micro: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VideoResult:
        return cls(
            id=data["id"],
            video_url=data.get("video_url"),
            model=data["model"],
            provider=data["provider"],
            cost=data.get("cost", 0.0),
            cache_hit=data.get("cache_hit", False),
            provider_cost_avoided_micro=data.get("provider_cost_avoided_micro"),
            latency_ms=data.get("latency_ms"),
            created_at=parse_datetime(data.get("created_at")),
        )

    def __repr__(self) -> str:
        return (
            f"VideoResult(id={self.id!r}, model={self.model!r}, "
            f"provider={self.provider!r})"
        )


class Videos:
    """Video generation resource (sync)."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        image_url: Optional[str] = None,
        duration_seconds: float = 5.0,
        skip_gcs_upload: bool = False,
        params: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> Union[VideoResult, GenerationRequest]:
        """Generate a video.

        Args:
            model: Model identifier (e.g. ``"fal-ai/flux-pro/video"``).
            prompt: Text description of the desired video.
            image_url: Optional image URL to animate (image-to-video).
            duration_seconds: Video duration in seconds. Defaults to 5.0.
            skip_gcs_upload: If True, return provider URL directly (faster; avoids proxy timeout).
            params: Additional model-specific parameters.
            wait: If True (default), block until complete. If False, return 202 and a
                GenerationRequest; poll with ``client.requests.get(request_id, wait=True)``
                or ``result.wait()``.

        Returns:
            VideoResult when wait=True, or GenerationRequest when wait=False.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
        }
        if image_url:
            payload["image_url"] = image_url
        if skip_gcs_upload:
            payload["skip_gcs_upload"] = True
        if params:
            payload.update(params)

        kwargs: Dict[str, Any] = {"json": payload}
        if not wait:
            kwargs["headers"] = {"Prefer": "respond-async"}

        data = self._client._request("POST", "/videos/generate", **kwargs)
        if data.get("request_id") and data.get("status") == "pending":
            return GenerationRequest(request_id=data["request_id"], client=self._client)
        return VideoResult.from_dict(data)


class AsyncVideos:
    """Video generation resource (async)."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        image_url: Optional[str] = None,
        duration_seconds: float = 5.0,
        skip_gcs_upload: bool = False,
        params: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> Union[VideoResult, AsyncGenerationRequest]:
        """Generate a video (async). See :meth:`Videos.generate` for details."""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
        }
        if image_url:
            payload["image_url"] = image_url
        if skip_gcs_upload:
            payload["skip_gcs_upload"] = True
        if params:
            payload.update(params)

        kwargs: Dict[str, Any] = {"json": payload}
        if not wait:
            kwargs["headers"] = {"Prefer": "respond-async"}

        data = await self._client._request("POST", "/videos/generate", **kwargs)
        if data.get("request_id") and data.get("status") == "pending":
            return AsyncGenerationRequest(
                request_id=data["request_id"], client=self._client
            )
        return VideoResult.from_dict(data)
