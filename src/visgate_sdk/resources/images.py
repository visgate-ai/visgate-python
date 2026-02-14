"""Image generation: ``POST /images/generate``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from visgate_sdk._utils import parse_datetime
from visgate_sdk.resources.requests import AsyncGenerationRequest, GenerationRequest

if TYPE_CHECKING:
    from datetime import datetime

    from visgate_sdk.client import AsyncClient, Client


@dataclass
class ImageResult:
    """Result of an image generation request.

    Attributes:
        id: Unique request identifier.
        images: List of generated image URLs.
        model: Model identifier used.
        provider: Provider name (e.g. ``"fal"``).
        cost: Cost in USD.
        cache_hit: Whether the result was served from cache.
        provider_cost_avoided_micro: When cache_hit is True, provider cost avoided in micro-USD (1e-6 USD).
        latency_ms: Server-side latency in milliseconds.
        created_at: Timestamp of the request.
        output_storage: Host/domain where output is stored (e.g. provider CDN). Present when API returns it.
        output_size_bytes: Size of primary output in bytes, when available.
        steps: Per-step timing/metadata (cache, provider, storage). Present when include_steps=True.
    """

    id: str
    images: List[str]
    model: str
    provider: str
    cost: float
    cache_hit: bool = False
    provider_cost_avoided_micro: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    output_storage: Optional[str] = None
    output_size_bytes: Optional[int] = None
    steps: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImageResult:
        return cls(
            id=data["id"],
            images=data.get("images", []),
            model=data["model"],
            provider=data["provider"],
            cost=data.get("cost", 0.0),
            cache_hit=data.get("cache_hit", False),
            provider_cost_avoided_micro=data.get("provider_cost_avoided_micro"),
            latency_ms=data.get("latency_ms"),
            created_at=parse_datetime(data.get("created_at")),
            output_storage=data.get("output_storage"),
            output_size_bytes=data.get("output_size_bytes"),
            steps=data.get("steps"),
        )

    def __repr__(self) -> str:
        return (
            f"ImageResult(id={self.id!r}, model={self.model!r}, "
            f"provider={self.provider!r}, images={len(self.images)})"
        )


class Images:
    """Image generation resource (sync)."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        seed: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        include_steps: bool = False,
        wait: bool = True,
    ) -> Union[ImageResult, GenerationRequest]:
        """Generate image(s).

        Args:
            model: Model identifier (e.g. ``"fal-ai/flux/schnell"``).
            prompt: Text description of the desired image.
            negative_prompt: What to avoid in the generated image.
            width: Image width in pixels. Defaults to 1024.
            height: Image height in pixels. Defaults to 1024.
            num_images: Number of images to generate. Defaults to 1.
            seed: Random seed for reproducibility.
            params: Additional model-specific parameters.
            include_steps: If True, response includes step timing (cache/provider/storage) in result.steps.
            wait: If True (default), block until complete. If False, return 202 and a
                GenerationRequest; poll with ``client.requests.get(request_id, wait=True)`` or ``result.wait()``.

        Returns:
            ImageResult when wait=True, or GenerationRequest when wait=False.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed
        if params:
            payload.update(params)

        kwargs: Dict[str, Any] = {"json": payload}
        if include_steps:
            kwargs["params"] = {"include_steps": "true"}
        if not wait:
            kwargs["headers"] = {"Prefer": "respond-async"}

        data = self._client._request("POST", "/images/generate", **kwargs)
        if data.get("request_id") and data.get("status") == "pending":
            return GenerationRequest(request_id=data["request_id"], client=self._client)
        return ImageResult.from_dict(data)


class AsyncImages:
    """Image generation resource (async)."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        seed: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        include_steps: bool = False,
        wait: bool = True,
    ) -> Union[ImageResult, AsyncGenerationRequest]:
        """Generate image(s). See :meth:`Images.generate` for details."""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed
        if params:
            payload.update(params)

        kwargs: Dict[str, Any] = {"json": payload}
        if include_steps:
            kwargs["params"] = {"include_steps": "true"}
        if not wait:
            kwargs["headers"] = {"Prefer": "respond-async"}

        data = await self._client._request("POST", "/images/generate", **kwargs)
        if data.get("request_id") and data.get("status") == "pending":
            return AsyncGenerationRequest(
                request_id=data["request_id"], client=self._client
            )
        return ImageResult.from_dict(data)
