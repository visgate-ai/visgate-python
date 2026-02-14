"""Unit tests for visgate-sdk."""
from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from visgate_sdk import Client, AsyncClient, __version__
from visgate_sdk.client import _handle_response, _resolve_api_key, _get_version
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
from visgate_sdk.resources.models import ModelInfo, ModelsResponse
from visgate_sdk.resources.requests import RequestStatusResult
from visgate_sdk.resources.providers import (
    ProviderBalanceItem,
    ProviderKeyInfo,
    ProviderKeysResponse,
    ProviderValidationResult,
)
from visgate_sdk.resources.usage import UsageSummary
from visgate_sdk.resources.videos import VideoResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, json_data=None, text="", headers=None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = Exception("No JSON")
    return resp


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def test_version():
    assert __version__, "Version should not be empty"
    parts = __version__.split(".")
    assert len(parts) >= 2, f"Version should be semver, got: {__version__}"


def test_version_fallback():
    v = _get_version()
    assert v, "Version fallback should return a non-empty string"


# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------

def test_resolve_api_key_from_argument():
    assert _resolve_api_key("vg-test") == "vg-test"


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("VISGATE_API_KEY", "vg-from-env")
    assert _resolve_api_key(None) == "vg-from-env"


def test_resolve_api_key_raises_without_key(monkeypatch):
    monkeypatch.delenv("VISGATE_API_KEY", raising=False)
    with pytest.raises(AuthenticationError, match="No API key"):
        _resolve_api_key(None)


def test_resolve_api_key_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("VISGATE_API_KEY", "vg-from-env")
    assert _resolve_api_key("vg-explicit") == "vg-explicit"


# ---------------------------------------------------------------------------
# Client instantiation
# ---------------------------------------------------------------------------

def test_client_instantiates():
    client = Client(api_key="test-key", base_url="https://example.com/api")
    assert client.base_url == "https://example.com/api"
    assert client.api_key == "test-key"
    client.close()


def test_client_strips_trailing_slash():
    client = Client(api_key="k", base_url="https://example.com/api/")
    assert client.base_url == "https://example.com/api"
    client.close()


def test_client_default_base_url():
    client = Client(api_key="k")
    assert client.base_url == "https://visgateai.com/api/v1"
    client.close()


def test_client_from_env(monkeypatch):
    monkeypatch.setenv("VISGATE_API_KEY", "vg-env-test")
    client = Client()
    assert client.api_key == "vg-env-test"
    client.close()


def test_client_has_all_resources():
    client = Client(api_key="k")
    assert client.images is not None
    assert client.models is not None
    assert client.videos is not None
    assert client.requests is not None
    assert client.usage is not None
    assert client.providers is not None
    client.close()


def test_client_fal_key_header():
    client = Client(api_key="k", fal_key="fal-test")
    headers = dict(client._client.headers)
    assert headers.get("x-fal-key") == "fal-test"
    client.close()


def test_client_replicate_key_header():
    client = Client(api_key="k", replicate_key="rep-test")
    headers = dict(client._client.headers)
    assert headers.get("x-replicate-key") == "rep-test"
    client.close()


def test_client_runway_key_header():
    client = Client(api_key="k", runway_key="rw-test")
    headers = dict(client._client.headers)
    assert headers.get("x-runway-key") == "rw-test"
    client.close()


def test_client_user_agent():
    client = Client(api_key="k")
    ua = dict(client._client.headers).get("user-agent", "")
    assert ua.startswith("visgate-sdk-python/")
    client.close()


def test_client_max_retries_default():
    client = Client(api_key="k")
    assert client.max_retries == 2
    client.close()


def test_client_max_retries_custom():
    client = Client(api_key="k", max_retries=0)
    assert client.max_retries == 0
    client.close()


def test_client_context_manager():
    with Client(api_key="k") as client:
        assert client is not None


def test_client_repr():
    client = Client(api_key="k")
    assert "visgateai.com" in repr(client)
    client.close()


def test_client_generate_method():
    """generate() should be a proper method, not just a resource."""
    client = Client(api_key="k")
    assert callable(client.generate)
    client.close()


def test_client_health_method():
    """health() should be a proper method."""
    client = Client(api_key="k")
    assert callable(client.health)
    client.close()


# ---------------------------------------------------------------------------
# Response handling (_handle_response is now a module function)
# ---------------------------------------------------------------------------

def test_handle_200():
    data = {"status": "ok"}
    resp = _mock_response(200, json_data=data)
    assert _handle_response(resp) == data


def test_handle_401():
    resp = _mock_response(401)
    with pytest.raises(AuthenticationError):
        _handle_response(resp)


def test_handle_422():
    resp = _mock_response(
        422, json_data={"message": "Invalid prompt", "details": {"field": "prompt"}}
    )
    with pytest.raises(ValidationError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.field == "prompt"


def test_handle_429_with_retry():
    resp = _mock_response(429, headers={"Retry-After": "30"})
    with pytest.raises(RateLimitError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.retry_after == 30


def test_handle_429_without_retry():
    resp = _mock_response(429, headers={})
    with pytest.raises(RateLimitError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.retry_after is None


def test_handle_provider_error():
    resp = _mock_response(
        502,
        json_data={
            "error": "PROVIDER_FAILURE",
            "message": "Fal timed out",
            "details": {"provider": "fal"},
        },
    )
    with pytest.raises(ProviderError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.provider == "fal"


def test_handle_generic_api_error():
    resp = _mock_response(400, json_data={"error": "BAD_REQUEST", "message": "Invalid param"})
    with pytest.raises(VisgateError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.error_code == "BAD_REQUEST"


def test_handle_non_json_error():
    resp = _mock_response(500, json_data=None, text="Internal Server Error")
    with pytest.raises(VisgateError) as exc_info:
        _handle_response(resp)
    assert "HTTP_500" in exc_info.value.error_code


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

def test_visgate_error_str():
    err = VisgateError("test msg", error_code="TEST")
    assert str(err) == "[TEST] test msg"
    assert err.message == "test msg"
    assert err.error_code == "TEST"
    assert err.details == {}
    assert err.status_code is None


def test_visgate_error_repr():
    err = VisgateError("test msg", error_code="TEST")
    assert "VisgateError" in repr(err)


def test_authentication_error():
    err = AuthenticationError()
    assert err.error_code == "AUTHENTICATION_ERROR"
    assert err.status_code == 401


def test_validation_error():
    err = ValidationError("bad field", field="prompt")
    assert err.error_code == "VALIDATION_ERROR"
    assert err.field == "prompt"
    assert err.status_code == 422


def test_rate_limit_error():
    err = RateLimitError(retry_after=60)
    assert err.retry_after == 60
    assert err.details == {"retry_after": 60}
    assert err.status_code == 429


def test_provider_error():
    err = ProviderError("fail", provider="replicate")
    assert err.provider == "replicate"
    assert err.details == {"provider": "replicate"}


def test_timeout_error():
    err = TimeoutError("timed out")
    assert err.error_code == "TIMEOUT_ERROR"


def test_connection_error():
    err = ConnectionError("network down")
    assert err.error_code == "CONNECTION_ERROR"


# ---------------------------------------------------------------------------
# Data classes (from_dict)
# ---------------------------------------------------------------------------

def test_generate_result_from_dict():
    data = {
        "id": "gen-1",
        "image_url": "https://img.test/1.png",
        "images": ["https://img.test/1.png"],
        "model": "fal-ai/flux/schnell",
        "latency_ms": 1200,
        "estimated_cost_usd": 0.003,
        "cost_per_megapixel_usd": 0.005,
        "resolution": {"width": 1024, "height": 1024},
        "provider": "fal",
        "mode": "managed",
        "created_at": "2026-01-01T00:00:00Z",
    }
    result = GenerateResult.from_dict(data)
    assert result.id == "gen-1"
    assert result.image_url == "https://img.test/1.png"
    assert result.cost == 0.003
    assert result.provider == "fal"
    assert result.mode == "managed"
    assert result.created_at is not None
    assert "gen-1" in repr(result)


def test_model_info_from_dict():
    data = {
        "id": "fal-ai/flux/schnell",
        "name": "FLUX Schnell",
        "provider": "fal",
        "media_type": "image",
        "tags": ["fast", "text-to-image"],
        "run_count": 5000,
    }
    model = ModelInfo.from_dict(data)
    assert model.id == "fal-ai/flux/schnell"
    assert model.provider == "fal"
    assert "fast" in model.tags
    assert "fal-ai/flux/schnell" in repr(model)


def test_models_response_from_dict():
    data = {
        "models": [
            {"id": "m1", "name": "M1", "provider": "fal", "media_type": "image"},
            {"id": "m2", "name": "M2", "provider": "replicate", "media_type": "video"},
        ],
        "total_count": 2,
    }
    resp = ModelsResponse.from_dict(data)
    assert resp.total_count == 2
    assert len(resp.models) == 2


def test_models_response_with_featured():
    data = {
        "models": [],
        "total_count": 0,
        "featured": [
            {
                "title": "Popular",
                "key": "popular",
                "models": [{"id": "m1", "name": "M1", "provider": "fal", "media_type": "image"}],
            }
        ],
    }
    resp = ModelsResponse.from_dict(data)
    assert resp.featured is not None
    assert len(resp.featured) == 1
    assert resp.featured[0].title == "Popular"


def test_image_result_from_dict():
    data = {
        "id": "img-1",
        "images": ["https://img.test/a.png"],
        "model": "flux",
        "provider": "fal",
        "latency_ms": 800,
        "cache_hit": True,
        "cost": 0.002,
        "created_at": "2026-01-01T00:00:00Z",
    }
    result = ImageResult.from_dict(data)
    assert result.id == "img-1"
    assert result.cache_hit is True
    assert result.cost == 0.002
    assert result.created_at is not None
    assert "img-1" in repr(result)


def test_video_result_from_dict():
    data = {
        "id": "vid-1",
        "video_url": "https://vid.test/v.mp4",
        "model": "runway-gen3",
        "provider": "runway",
        "latency_ms": 15000,
        "cache_hit": False,
        "cost": 0.05,
        "created_at": "2026-01-01T00:00:00Z",
    }
    result = VideoResult.from_dict(data)
    assert result.id == "vid-1"
    assert result.video_url == "https://vid.test/v.mp4"
    assert result.provider == "runway"
    assert "vid-1" in repr(result)


def test_request_status_result_from_dict():
    data = {
        "request_id": "req-123",
        "status": "completed",
        "media_type": "video",
        "provider": "fal",
        "model": "fal-ai/veo3",
        "output_url": "https://storage.example/v.mp4",
        "error_message": None,
    }
    result = RequestStatusResult.from_dict(data)
    assert result.request_id == "req-123"
    assert result.status == "completed"
    assert result.media_type == "video"
    assert result.output_url == "https://storage.example/v.mp4"
    assert result.is_terminal is True
    assert "req-123" in repr(result)


def test_usage_summary_from_dict():
    data = {
        "total_requests": 100,
        "successful_requests": 95,
        "failed_requests": 5,
        "cached_requests": 20,
        "total_provider_cost": 1.0,
        "total_billed_cost": 1.2,
        "total_savings": 0.2,
        "period": "month",
    }
    summary = UsageSummary.from_dict(data)
    assert summary.total_requests == 100
    assert summary.cache_hit_rate == 20.0
    assert summary.total_billed_cost == 1.2
    assert "month" in repr(summary)


def test_usage_summary_zero_requests():
    summary = UsageSummary.from_dict({"total_requests": 0})
    assert summary.cache_hit_rate == 0.0


def test_usage_summary_backward_compat():
    data = {
        "total_requests": 10,
        "total_cost_usd": 0.5,
        "provider_breakdown": {"fal": 8, "replicate": 2},
    }
    summary = UsageSummary.from_dict(data)
    assert summary.total_billed_cost == 0.5
    assert summary.by_provider == {"fal": 8, "replicate": 2}


def test_provider_key_info_from_dict():
    data = {"provider": "fal", "validated": True, "masked_key": "fal_...abc"}
    info = ProviderKeyInfo.from_dict(data)
    assert info.provider == "fal"
    assert info.validated is True


def test_provider_keys_response_from_dict():
    data = {"keys": [{"provider": "fal", "validated": True}]}
    resp = ProviderKeysResponse.from_dict(data)
    assert len(resp.keys) == 1


def test_provider_balance_from_dict():
    data = {
        "provider": "replicate",
        "configured": True,
        "available": True,
        "remaining": 5.0,
        "currency": "USD",
    }
    balance = ProviderBalanceItem.from_dict(data)
    assert balance.provider == "replicate"
    assert balance.remaining == 5.0


def test_provider_validation_result_from_dict():
    data = {"valid": True, "message": "Key is valid"}
    result = ProviderValidationResult.from_dict(data)
    assert result.valid is True


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------

def test_async_client_instantiates():
    client = AsyncClient(api_key="test-key")
    assert client.base_url == "https://visgateai.com/api/v1"
    assert client.images is not None
    assert client.models is not None


def test_async_client_from_env(monkeypatch):
    monkeypatch.setenv("VISGATE_API_KEY", "vg-env-async")
    client = AsyncClient()
    assert client.api_key == "vg-env-async"


def test_async_client_repr():
    client = AsyncClient(api_key="k")
    assert "AsyncClient" in repr(client)


@pytest.mark.asyncio
async def test_async_client_context_manager():
    async with AsyncClient(api_key="k") as client:
        assert client is not None
