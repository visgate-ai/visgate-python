"""Usage and billing: ``GET /usage``, ``GET /usage/logs``, ``GET /dashboard``."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from visgate_sdk._utils import parse_datetime

if TYPE_CHECKING:
    from datetime import datetime

    from visgate_sdk.client import AsyncClient, Client


@dataclass
class UsageSummary:
    """Usage statistics for a time period.

    Attributes:
        total_requests: Total number of API requests.
        successful_requests: Number of successful requests.
        failed_requests: Number of failed requests.
        cached_requests: Number of requests served from cache.
        total_provider_cost: Total cost paid to providers.
        total_billed_cost: Total cost billed to the user.
        total_savings: Savings from caching.
        by_provider: Request counts broken down by provider.
        by_model: Request counts broken down by model.
        period: Time period (``"day"``, ``"week"``, ``"month"``, ``"year"``).
        period_start: Start of the reporting period.
        period_end: End of the reporting period.
    """

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_provider_cost: float = 0.0
    total_billed_cost: float = 0.0
    total_savings: float = 0.0
    by_provider: Dict[str, int] = field(default_factory=dict)
    by_model: Dict[str, int] = field(default_factory=dict)
    period: str = "month"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as a percentage (0--100)."""
        if self.total_requests == 0:
            return 0.0
        return (self.cached_requests / self.total_requests) * 100

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UsageSummary:
        return cls(
            total_requests=data.get("total_requests", 0),
            successful_requests=data.get("successful_requests", 0),
            failed_requests=data.get("failed_requests", 0),
            cached_requests=data.get("cached_requests", 0),
            total_provider_cost=data.get("total_provider_cost", 0.0),
            total_billed_cost=data.get("total_billed_cost", data.get("total_cost_usd", 0.0)),
            total_savings=data.get("total_savings", 0.0),
            by_provider=data.get("by_provider", data.get("provider_breakdown", {})),
            by_model=data.get("by_model", {}),
            period=data.get("period", "month"),
            period_start=parse_datetime(data.get("period_start")),
            period_end=parse_datetime(data.get("period_end")),
        )

    def __repr__(self) -> str:
        return (
            f"UsageSummary(period={self.period!r}, requests={self.total_requests}, "
            f"cost=${self.total_billed_cost:.4f})"
        )


class Usage:
    """Usage and billing resource (sync)."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def get(self, period: str = "month") -> UsageSummary:
        """Get usage summary for a time period.

        Args:
            period: ``"day"``, ``"week"``, ``"month"``, or ``"year"``.

        Returns:
            UsageSummary with aggregated statistics.
        """
        data = self._client._request("GET", "/usage", params={"period": period})
        return UsageSummary.from_dict(data)

    def logs(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get detailed usage logs.

        Args:
            limit: Maximum number of log entries to return.
            offset: Number of entries to skip for pagination.

        Returns:
            List of log entry dicts.
        """
        data = self._client._request(
            "GET", "/usage/logs", params={"limit": limit, "offset": offset}
        )
        return data if isinstance(data, list) else data.get("logs", [])

    def dashboard(self, period: str = "month") -> Dict[str, Any]:
        """Get dashboard summary data.

        Args:
            period: ``"day"``, ``"week"``, ``"month"``, or ``"year"``.

        Returns:
            Dict with dashboard metrics.
        """
        return self._client._request("GET", "/dashboard", params={"period": period})


class AsyncUsage:
    """Usage and billing resource (async)."""

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def get(self, period: str = "month") -> UsageSummary:
        """Get usage summary (async). See :meth:`Usage.get` for details."""
        data = await self._client._request("GET", "/usage", params={"period": period})
        return UsageSummary.from_dict(data)

    async def logs(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get detailed usage logs (async). See :meth:`Usage.logs` for details."""
        data = await self._client._request(
            "GET", "/usage/logs", params={"limit": limit, "offset": offset}
        )
        return data if isinstance(data, list) else data.get("logs", [])

    async def dashboard(self, period: str = "month") -> Dict[str, Any]:
        """Get dashboard summary (async). See :meth:`Usage.dashboard` for details."""
        return await self._client._request("GET", "/dashboard", params={"period": period})
