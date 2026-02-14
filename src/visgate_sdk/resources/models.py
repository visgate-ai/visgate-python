"""Model catalog: ``GET /models``."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from visgate_sdk.client import AsyncClient, Client


@dataclass
class ModelInfo:
    """Rich model information."""
    id: str
    name: str
    provider: str
    media_type: str

    # Metadata
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    cover_image_url: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None

    # Pricing
    base_cost_micro: int = 0
    normalized_cost_micro: int = 0
    pricing: Optional[str] = None
    pricing_unit: Optional[str] = None

    # Usage
    run_count: int = 0

    # Capabilities
    input_types: List[str] = field(default_factory=list)
    output_type: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)

    # Timestamps
    first_seen_at: Optional[str] = None
    provider_created_at: Optional[str] = None
    last_synced_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelInfo:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            provider=data.get("provider", ""),
            media_type=data.get("media_type", "image"),
            description=data.get("description"),
            category=data.get("category"),
            tags=data.get("tags", []),
            cover_image_url=data.get("cover_image_url"),
            author=data.get("author"),
            url=data.get("url"),
            base_cost_micro=data.get("base_cost_micro", 0),
            normalized_cost_micro=data.get("normalized_cost_micro", 0),
            pricing=data.get("pricing"),
            pricing_unit=data.get("pricing_unit"),
            run_count=data.get("run_count", 0),
            input_types=data.get("input_types", []),
            output_type=data.get("output_type"),
            capabilities=data.get("capabilities", []),
            first_seen_at=data.get("first_seen_at"),
            provider_created_at=data.get("provider_created_at"),
            last_synced_at=data.get("last_synced_at"),
        )

    def __repr__(self) -> str:
        return f"ModelInfo(id={self.id!r}, provider={self.provider!r}, media_type={self.media_type!r})"


@dataclass
class FeaturedSection:
    """A curated section of models."""
    title: str
    key: str
    models: List[ModelInfo]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeaturedSection":
        return cls(
            title=data.get("title", ""),
            key=data.get("key", ""),
            models=[ModelInfo.from_dict(m) for m in data.get("models", [])],
        )


@dataclass
class ModelsResponse:
    """Response from models.list()."""
    models: List[ModelInfo]
    total_count: int = 0
    last_updated: Optional[str] = None
    featured: Optional[List[FeaturedSection]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelsResponse":
        featured_raw = data.get("featured")
        featured = [FeaturedSection.from_dict(s) for s in featured_raw] if featured_raw else None
        return cls(
            models=[ModelInfo.from_dict(m) for m in data.get("models", [])],
            total_count=data.get("total_count", 0),
            last_updated=data.get("last_updated"),
            featured=featured,
        )


class Models:
    """Models resource (sync)."""

    def __init__(self, client: "Client"):
        self._client = client

    def list(
        self,
        *,
        provider: Optional[str] = None,
        media_type: Optional[str] = None,
        model_type: Optional[str] = None,
        capability: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 100,
        featured: bool = False,
    ) -> ModelsResponse:
        """
        List available models from the API catalog (database).

        Args:
            provider: Filter by provider (fal, replicate, runway)
            media_type: Filter by type (image, video)
            model_type: Alias for media_type (e.g. model_type="video")
            capability: Filter by capability (text-to-image, image-to-video, etc.)
            search: Search by name or description
            sort: Sort by (name, cost, newest, popular)
            limit: Max results (default 100)
            featured: Include featured/curated sections

        Returns:
            ModelsResponse with models list and optional featured sections
        """
        if model_type is not None and media_type is None:
            media_type = model_type
        params: Dict[str, Any] = {"limit": limit}
        if provider:
            params["provider"] = provider
        if media_type:
            params["media_type"] = media_type
        if capability:
            params["capability"] = capability
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        if featured:
            params["featured"] = "true"

        data = self._client._request("GET", "/models", params=params)
        return ModelsResponse.from_dict(data)

    def get(self, model_id: str) -> ModelInfo:
        """
        Get detailed information for a specific model.

        Args:
            model_id: Model ID (e.g., "fal-ai/flux-pro", "black-forest-labs/flux-schnell")

        Returns:
            ModelInfo with full model details
        """
        data = self._client._request("GET", f"/models/{model_id}")
        return ModelInfo.from_dict(data)

    def search(self, query: str, *, limit: int = 20) -> ModelsResponse:
        """
        Search models by name, description, or author.
        Shorthand for models.list(search=query).

        Args:
            query: Search term
            limit: Max results

        Returns:
            ModelsResponse with matching models
        """
        return self.list(search=query, limit=limit)


class AsyncModels:
    """Models resource (async)."""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def list(
        self,
        *,
        provider: Optional[str] = None,
        media_type: Optional[str] = None,
        model_type: Optional[str] = None,
        capability: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 100,
        featured: bool = False,
    ) -> ModelsResponse:
        """List available models (async). See Models.list for details."""
        if model_type is not None and media_type is None:
            media_type = model_type
        params: Dict[str, Any] = {"limit": limit}
        if provider:
            params["provider"] = provider
        if media_type:
            params["media_type"] = media_type
        if capability:
            params["capability"] = capability
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        if featured:
            params["featured"] = "true"

        data = await self._client._request("GET", "/models", params=params)
        return ModelsResponse.from_dict(data)

    async def get(self, model_id: str) -> ModelInfo:
        """Get detailed info for a model (async). See Models.get for details."""
        data = await self._client._request("GET", f"/models/{model_id}")
        return ModelInfo.from_dict(data)

    async def search(self, query: str, *, limit: int = 20) -> ModelsResponse:
        """Search models (async). Shorthand for list(search=query)."""
        return await self.list(search=query, limit=limit)
