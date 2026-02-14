# API reference

Short reference for the **visgate-python** SDK. Full OpenAPI spec: **https://visgateai.com/api/v1/docs** (or your base URL + `/docs`).

## Testing against the live API

Use the SDK and the numbered examples to hit the live API. Sample outputs use an **Istanbul theme** (Bosphorus, Galata Tower, golden hour).

```bash
pip install visgate-sdk
export VISGATE_API_KEY=vg-...

# Health and models (no auth)
python examples/01_live_api_smoke.py

# Auth and identity
python examples/00_auth_identity.py

# Run all examples (requires API key; generation steps incur cost)
python examples/run_all_capabilities.py
```

**Run with a credentials file (e.g. `.env` in repo root):**

```bash
python examples/run_with_env.py
python examples/run_with_env.py 04_videos_all_providers.py   # single example
```

**Low-cost run (no image/video generation):** `00_smoke_sdk`, `01_live_api_smoke`, `00_auth_identity`, `01_models_catalog`, `05_usage_history_verify`, `06_provider_balances`, `09_provider_keys`, `10_api_keys`, `11_billing_readonly`. See the [main README (Examples section)](../README.md#examples) for the full table and sample outputs.

Base URL defaults to `https://visgateai.com/api/v1`. Override with `VISGATE_BASE_URL` for staging or local.

## Installation

```bash
pip install visgate-sdk
```

## Client

### Synchronous Client

```python
from visgate_sdk import Client

client = Client(
    api_key="your_visgate_api_key",
    base_url="https://visgateai.com/api/v1",  # Optional, defaults to production
    timeout=120.0,  # Optional, request timeout in seconds
    fal_key=None,  # Optional, for BYOK mode (see below)
)
```

### Asynchronous Client

```python
from visgate_sdk import AsyncClient
import asyncio

async def main():
    async with AsyncClient(
        api_key="your_visgate_api_key",
        base_url="https://visgateai.com/api/v1",
        timeout=120.0,
        fal_key=None,
    ) as client:
        # Use client here
        result = await client.generate(prompt="a sunset")
        print(result.images)

asyncio.run(main())
```

### BYOK Mode (Bring Your Own Key)

Use your own provider API keys while still using visgate for billing and features:

```python
from visgate_sdk import Client

# Provide your FAL.ai API key for BYOK mode
client = Client(
    api_key="your_visgate_api_key",  # Required for billing
    fal_key="your_fal_api_key",  # Your provider key
)

# Requests use your provider key, but visgate bills base fee
result = client.generate(prompt="a cat", model="fal-ai/flux/schnell")
# result.mode will be "byok"
```

**Note:** BYOK mode requires both a visgate API key (for authentication and base fee billing) and a provider key (for the actual generation).

## Generate (Unified Image Generation)

Simplified endpoint for quick image generation.

### Sync

```python
result = client.generate(
    prompt="a beautiful sunset over mountains",
    model="fal-ai/flux/schnell",  # Optional, defaults to "fal-ai/flux/schnell"
    params=None,  # Optional, model-specific parameters
)

# result: GenerateResult
print(result.images)  # List of image URLs
print(result.image_url)  # First image URL (convenience)
print(result.mode)  # "managed" or "byok"
print(result.provider)  # Provider name (e.g., "fal")
print(result.cost)  # Estimated cost in USD
print(result.latency_ms)  # Request latency in milliseconds
```

### Async

```python
result = await client.generate(
    prompt="a beautiful sunset over mountains",
    model="fal-ai/flux/schnell",
    params={"num_images": 2, "image_size": "1024x1024"},
)
```

### GenerateResult Properties

- `id` (str): Request ID
- `images` (list[str]): List of generated image URLs
- `image_url` (str | None): First image URL (convenience property)
- `model` (str): Model identifier used
- `provider` (str): Provider name (e.g., "fal", "replicate")
- `mode` (str): "managed" or "byok"
- `cost` (float): Estimated cost in USD
- `cost_per_megapixel` (float): Cost per megapixel
- `latency_ms` (int): Request latency in milliseconds
- `resolution` (dict): Dict with "width" and "height" keys
- `created_at` (str): ISO timestamp

## Images Resource

Full-featured image generation with all parameters.

### Sync

```python
result = client.images.generate(
    model="fal-ai/flux/schnell",
    prompt="a futuristic city at night",
    negative_prompt=None,  # Optional, what to avoid in the image
    width=1024,  # Optional, default 1024
    height=1024,  # Optional, default 1024
    num_images=1,  # Optional, default 1
    seed=None,  # Optional, for reproducibility
    params=None,  # Optional, additional model-specific parameters
    include_steps=False,  # Optional, if True response includes step timing (cache/provider/storage)
)
```

### Async

```python
result = await client.images.generate(
    model="fal-ai/flux/schnell",
    prompt="a futuristic city at night",
    width=1024,
    height=1024,
    num_images=1,
    include_steps=False,  # Set True to get step timing in result.steps
)
```

### ImageResult Properties

- `id` (str): Request ID
- `images` (list[str]): List of generated image URLs
- `model` (str): Model identifier used
- `provider` (str): Provider name
- `cost` (float): Cost in USD
- `cache_hit` (bool): Whether the result was served from cache (same model+prompt+size returns cached result with lower latency).
- `provider_cost_avoided_micro` (int | None): When `cache_hit` is true, provider cost avoided in micro-USD (1e-6 USD). Omitted on cache miss.
- `latency_ms` (int | None): Request latency in milliseconds
- `created_at` (datetime): Creation timestamp
- `output_storage` (str | None): Host/domain where the output is stored (e.g. `storage.googleapis.com` or provider CDN). Present when the API returns it.
- `output_size_bytes` (int | None): Size of the primary output in bytes, when available.
- `steps` (list | None): Per-step timing and metadata (e.g. cache lookup, provider call, storage). Only present when `include_steps=True` was passed.

## Cache

- **Scope:** Cache is **org-scoped** by default (`VISGATE_CACHE_SCOPE=org`). Keys include organization ID so different orgs do not share cache. Set `VISGATE_CACHE_SCOPE=global` to share cache across organizations. TTL is configurable; `VISGATE_CACHE_TTL_SECONDS=0` means never expire.
- **Exact cache:** Same model + prompt + size → same cache key. Second request returns from cache (lower latency); response includes `cache_hit: true` and `provider_cost_avoided_micro` (cost saved in micro-USD). Example: `examples/07_cache_demo.py`.
- **Semantic cache:** Similar wording, different text. The API uses Vertex AI embeddings and Firestore to match prompts; when similarity is above threshold, the result is served from cache and the provider is not called. Response includes `cache_hit: true` and `provider_cost_avoided_micro`. Different models’ results can be reused (no model filter). Example: `examples/08_semantic_cache_demo.py`.

## Videos Resource

Generate videos from prompts or images.

### Sync

```python
result = client.videos.generate(
    model="fal-ai/flux-pro/video",
    prompt="a cat walking",
    image_url=None,  # Optional, image URL to animate
    duration_seconds=5.0,  # Optional, default 5.0
    skip_gcs_upload=False,  # Set True to return provider URL directly (faster, avoids proxy timeouts)
    params=None,  # Optional, additional model-specific parameters
)
```

### Async

```python
result = await client.videos.generate(
    model="fal-ai/flux-pro/video",
    prompt="a bird flying",
    duration_seconds=5.0,
)
```

### VideoResult Properties

- `id` (str): Request ID
- `video_url` (str | None): Generated video URL (may be ``None`` if generation failed or still processing)
- `model` (str): Model identifier used
- `provider` (str): Provider name (e.g. ``"fal"``, ``"replicate"``, ``"runway"``)
- `cost` (float): Cost in USD
- `cache_hit` (bool): Whether the result was served from cache
- `provider_cost_avoided_micro` (int | None): When `cache_hit` is true, provider cost avoided in micro-USD. Omitted on cache miss.
- `latency_ms` (int | None): Request latency in milliseconds
- `created_at` (datetime): Creation timestamp

**Note:** Video generation can take a minute or more. Use `skip_gcs_upload=True` to get the provider URL directly and avoid proxy timeouts. For non-blocking flow, use `wait=False` and poll via the Requests resource (see below).

### Async 202 + poll (wait=False)

For long-running video or image generation, use `wait=False` to get a 202 response and a `GenerationRequest`; then poll until complete:

```python
req = client.videos.generate(
    model="fal-ai/veo3",
    prompt="Cinematic drone over Istanbul",
    duration_seconds=5.0,
    wait=False,
)
# req has .request_id and .status ("accepted", "processing", "completed", "failed")
result = req.wait()  # blocks until completed, returns VideoResult
print(result.video_url)

# Or poll manually
status = client.requests.get(req.request_id, wait=True)
# status.result is VideoResult when status.status == "completed"
```

## Requests Resource

Poll async generation status (202 flow for videos/images).

### Sync

```python
req = client.requests.get(request_id)           # current status
req = client.requests.get(request_id, wait=True)  # block until completed
# req: RequestStatusResult with .request_id, .status, .result (VideoResult/ImageResult when completed)
```

### Async

```python
req = await client.requests.get(request_id)
req = await client.requests.get(request_id, wait=True)
```

### RequestStatusResult

- `request_id` (str): Request ID
- `status` (str): `"accepted"` | `"processing"` | `"completed"` | `"failed"`
- `result` (VideoResult | ImageResult | None): Output when status is `"completed"`
- `error` (dict | None): Error details when status is `"failed"`

Example: `examples/13_async_generation.py`.

## Usage Resource

Get usage statistics for your account.

### Sync

```python
summary = client.usage.get(period="month")  # "day" | "week" | "month" | "year"
```

### Async

```python
summary = await client.usage.get(period="month")
```

### UsageSummary Properties

- `period_start` (datetime): Start of the period
- `period_end` (datetime): End of the period
- `total_requests` (int): Total number of requests
- `successful_requests` (int): Number of successful requests
- `failed_requests` (int): Number of failed requests
- `cached_requests` (int): Number of requests served from cache
- `total_provider_cost` (float): Total cost paid to providers
- `total_billed_cost` (float): Total cost billed to you
- `total_savings` (float): Savings from cache hits
- `cache_hit_rate` (float): Cache hit rate as percentage (property)
- `by_provider` (dict[str, int]): Request counts by provider
- `by_model` (dict[str, int]): Request counts by model

### Example

```python
summary = client.usage.get(period="month")
print(f"Total requests: {summary.total_requests}")
print(f"Cache hit rate: {summary.cache_hit_rate:.1f}%")
print(f"Total cost: ${summary.total_billed_cost:.6f}")
print(f"By provider: {summary.by_provider}")
```

## Error Handling

All exceptions extend `VisgateError`. Handle errors appropriately:

```python
from visgate_sdk import Client
from visgate_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    ProviderError,
    ValidationError,
    VisgateError,
)

client = Client(api_key="your_api_key")

try:
    result = client.generate(prompt="a sunset", model="fal-ai/flux/schnell")
except AuthenticationError:
    print("Invalid or missing API key")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
except ProviderError as e:
    print(f"Provider error: {e.message} (provider: {e.provider})")
except ValidationError:
    print("Invalid request parameters")
except VisgateError as e:
    print(f"API error: {e.message} (code: {e.error_code})")
```

### Exception Types

| Exception | HTTP Status | When |
|-----------|-------------|------|
| `AuthenticationError` | 401 | Invalid or missing API key |
| `ValidationError` | 422 | Bad request parameters |
| `RateLimitError` | 429 | Too many requests (includes `retry_after` attribute) |
| `ProviderError` | 502 | Upstream provider (Fal, Replicate, Runway) failed |
| `VisgateError` | 404, 500, etc. | e.g. 404 + ``MODEL_NOT_FOUND`` for unsupported model; other API errors |

### Exception Properties

All exceptions have:
- `message` (str): Error message
- `error_code` (str): Error code
- `details` (dict | None): Additional error details

`RateLimitError` also has:
- `retry_after` (int | None): Seconds to wait before retrying

`ProviderError` also has:
- `provider` (str): Provider name that failed

## Context Managers

Both clients support context managers for automatic cleanup:

### Sync

```python
with Client(api_key="your_key") as client:
    result = client.generate(prompt="test")
    # Client automatically closed
```

### Async

```python
async with AsyncClient(api_key="your_key") as client:
    result = await client.generate(prompt="test")
    # Client automatically closed
```

## Examples

### Complete Example: Sync Client

```python
from visgate_sdk import Client

# Initialize client
client = Client(api_key="your_api_key")

# Generate image
result = client.generate(
    prompt="a beautiful sunset",
    model="fal-ai/flux/schnell",
    params={"num_images": 1}
)

print(f"Generated {len(result.images)} image(s)")
print(f"Cost: ${result.cost:.6f}")
print(f"Image URL: {result.image_url}")

# Get usage
summary = client.usage.get(period="month")
print(f"Total requests this month: {summary.total_requests}")
print(f"Cache hit rate: {summary.cache_hit_rate:.1f}%")

# Close client
client.close()
```

### Complete Example: Async Client

```python
from visgate_sdk import AsyncClient
import asyncio

async def main():
    async with AsyncClient(api_key="your_api_key") as client:
        # Generate image
        result = await client.generate(
            prompt="a beautiful sunset",
            model="fal-ai/flux/schnell"
        )
        print(f"Generated: {result.image_url}")
        
        # Get usage
        summary = await client.usage.get(period="month")
        print(f"Requests: {summary.total_requests}")

asyncio.run(main())
```

### BYOK Mode Example

```python
from visgate_sdk import Client

# Use your own FAL.ai key
client = Client(
    api_key="your_visgate_api_key",
    fal_key="your_fal_api_key",
)

# Generate with your key (visgate bills base fee only)
result = client.generate(
    prompt="a cat playing",
    model="fal-ai/flux/schnell"
)

print(f"Mode: {result.mode}")  # "byok"
print(f"Provider: {result.provider}")  # "fal"
print(f"Image: {result.image_url}")

client.close()
```

## Security & data

API traffic is over HTTPS. Provider keys (BYOK) are encrypted at rest; account and usage data are stored on Google Cloud with encryption at rest.

## Sample outputs (Istanbul theme)

Example scripts use Istanbul-themed prompts (Bosphorus, Galata Tower, golden hour). Generated assets are in `examples/sample_outputs/`: images (`generate_unified.jpg`, `sunset_istanbul.jpg`, `galata_tower.jpg`, `bosphorus_night.jpg`), cache demos (`cache_demo.jpg`, `semantic_exact.jpg`, `semantic_similar.jpg`), and video `istanbul.mp4`. See the [main README (Examples section)](../README.md#examples) for the output gallery and step-by-step guide.

## Additional resources

- SDK README: [README.md](../README.md)
- Examples (step-by-step and sample results): [README.md#examples](../README.md#examples)
- OpenAPI spec: **https://visgateai.com/api/v1/docs**
