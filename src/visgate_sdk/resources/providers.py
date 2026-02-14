"""Provider key management and balance resources."""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from visgate_sdk.client import Client, AsyncClient


@dataclass
class ProviderKeyInfo:
    provider: str
    validated: bool
    validated_at: Optional[str] = None
    masked_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderKeyInfo":
        return cls(
            provider=data.get("provider", ""),
            validated=bool(data.get("validated", False)),
            validated_at=data.get("validated_at"),
            masked_key=data.get("masked_key"),
        )


@dataclass
class ProviderKeysResponse:
    keys: List[ProviderKeyInfo]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderKeysResponse":
        return cls(keys=[ProviderKeyInfo.from_dict(k) for k in data.get("keys", [])])


@dataclass
class ProviderValidationResult:
    valid: bool
    message: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderValidationResult":
        return cls(valid=bool(data.get("valid", False)), message=str(data.get("message", "")))


@dataclass
class ProviderBalanceItem:
    provider: str
    configured: bool
    available: bool
    limit: Optional[float] = None
    remaining: Optional[float] = None
    currency: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderBalanceItem":
        return cls(
            provider=data.get("provider", ""),
            configured=bool(data.get("configured", False)),
            available=bool(data.get("available", False)),
            limit=data.get("limit"),
            remaining=data.get("remaining"),
            currency=data.get("currency"),
            message=data.get("message"),
        )


@dataclass
class ProviderBalancesResponse:
    balances: List[ProviderBalanceItem]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderBalancesResponse":
        return cls(balances=[ProviderBalanceItem.from_dict(b) for b in data.get("balances", [])])


class Providers:
    """Sync provider management resource."""

    def __init__(self, client: "Client"):
        self._client = client

    def list_keys(self) -> ProviderKeysResponse:
        data = self._client._request("GET", "/providers/keys")
        return ProviderKeysResponse.from_dict(data)

    def set_key(self, provider: str, api_key: str) -> ProviderKeyInfo:
        data = self._client._request(
            "PUT",
            "/providers/keys",
            json={"provider": provider, "api_key": api_key},
        )
        return ProviderKeyInfo.from_dict(data)

    def delete_key(self, provider: str) -> Dict[str, Any]:
        return self._client._request("DELETE", f"/providers/keys/{provider}")

    def validate_key(self, provider: str, api_key: str) -> ProviderValidationResult:
        data = self._client._request(
            "POST",
            "/providers/validate",
            json={"provider": provider, "api_key": api_key},
        )
        return ProviderValidationResult.from_dict(data)

    def balances(self) -> ProviderBalancesResponse:
        data = self._client._request("GET", "/providers/balances")
        return ProviderBalancesResponse.from_dict(data)


class AsyncProviders:
    """Async provider management resource."""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def list_keys(self) -> ProviderKeysResponse:
        data = await self._client._request("GET", "/providers/keys")
        return ProviderKeysResponse.from_dict(data)

    async def set_key(self, provider: str, api_key: str) -> ProviderKeyInfo:
        data = await self._client._request(
            "PUT",
            "/providers/keys",
            json={"provider": provider, "api_key": api_key},
        )
        return ProviderKeyInfo.from_dict(data)

    async def delete_key(self, provider: str) -> Dict[str, Any]:
        return await self._client._request("DELETE", f"/providers/keys/{provider}")

    async def validate_key(self, provider: str, api_key: str) -> ProviderValidationResult:
        data = await self._client._request(
            "POST",
            "/providers/validate",
            json={"provider": provider, "api_key": api_key},
        )
        return ProviderValidationResult.from_dict(data)

    async def balances(self) -> ProviderBalancesResponse:
        data = await self._client._request("GET", "/providers/balances")
        return ProviderBalancesResponse.from_dict(data)
