"""Unified image generation: ``POST /generate``."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from visgate_sdk._utils import parse_datetime

if TYPE_CHECKING:
    from datetime import datetime

    from visgate_sdk.client import AsyncClient, Client


@dataclass
class GenerateResult:
    """Result of a generation request.

    Attributes:
        id: Unique request identifier.
        image_url: URL of the first generated image (convenience shortcut).
        images: List of all generated image URLs.
        model: Model identifier used for generation.
        provider: Provider that served the request (e.g. ``"fal"``).
        mode: ``"managed"`` or ``"byok"``.
        cost: Estimated cost in USD.
        cost_per_megapixel: Cost per megapixel in USD.
        latency_ms: Server-side latency in milliseconds.
        resolution: Dict with ``"width"`` and ``"height"`` keys.
        created_at: Timestamp of the request.
    """

    id: str
    image_url: Optional[str]
    images: List[str]
    model: str
    provider: str
    mode: str
    cost: float
    cost_per_megapixel: float
    latency_ms: int
    resolution: Dict[str, int] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GenerateResult:
        return cls(
            id=data["id"],
            image_url=data.get("image_url"),
            images=data.get("images", []),
            model=data["model"],
            provider=data.get("provider", ""),
            mode=data.get("mode", ""),
            cost=data.get("estimated_cost_usd", 0.0),
            cost_per_megapixel=data.get("cost_per_megapixel_usd", 0.0),
            latency_ms=data.get("latency_ms", 0),
            resolution=data.get("resolution", {}),
            created_at=parse_datetime(data.get("created_at")),
        )

    def __repr__(self) -> str:
        return (
            f"GenerateResult(id={self.id!r}, model={self.model!r}, "
            f"provider={self.provider!r}, mode={self.mode!r}, cost={self.cost})"
        )


class Generate:
    """Sync unified generation resource."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def __call__(
        self,
        prompt: str,
        model: str = "fal-ai/flux/schnell",
        params: Optional[Dict[str, Any]] = None,
    ) -> GenerateResult:
        payload: Dict[str, Any] = {"prompt": prompt, "model": model}
        if params:
            payload["params"] = params
        data = self._client._request("POST", "/generate", json=payload)
        return GenerateResult.from_dict(data)


class AsyncGenerate:
    """Async unified generation resource."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def __call__(
        self,
        prompt: str,
        model: str = "fal-ai/flux/schnell",
        params: Optional[Dict[str, Any]] = None,
    ) -> GenerateResult:
        payload: Dict[str, Any] = {"prompt": prompt, "model": model}
        if params:
            payload["params"] = params
        data = await self._client._request("POST", "/generate", json=payload)
        return GenerateResult.from_dict(data)
