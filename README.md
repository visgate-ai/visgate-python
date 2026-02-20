# visgate-sdk

Python SDK for the [visgate API](https://visgateai.com) — one client for image and video generation across **Fal**, **Replicate**, and **Runway**.

[![CI](https://github.com/visgate-ai/visgate-python/actions/workflows/ci.yml/badge.svg)](https://github.com/visgate-ai/visgate-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/visgate-sdk)](https://pypi.org/project/visgate-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/visgate-sdk)](https://pypi.org/project/visgate-sdk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

visgate is a vision ai gateway: one API, one SDK, three providers. Generate images and videos with Fal, Replicate, or Runway — managed keys or bring your own. Built-in cache, usage tracking, and typed exceptions.

## Install

```bash
pip install visgate-sdk
```

## Quick Start

```python
from visgate_sdk import Client

client = Client()  # reads VISGATE_API_KEY from environment

result = client.generate("a sunset over Istanbul")
print(result.image_url)

client.close()
```

With a context manager:

```python
with Client() as client:
    result = client.generate("a sunset over Istanbul", model="fal-ai/flux/schnell")
    print(result.image_url, result.cost, result.provider)
```

## Features

- **One client, three providers.** Fal, Replicate, and Runway behind a single API.
- **Managed and BYOK modes.** Use visgate-managed keys or bring your own.
- **Sync and async.** `Client` for sync, `AsyncClient` for async.
- **Async 202 + poll.** `videos.generate(wait=False)` / `images.generate(wait=False)` for long-running jobs; poll with `client.requests.get()`.
- **Automatic retries.** Transient errors (429, 5xx) with exponential backoff.
- **Typed exceptions.** `AuthenticationError`, `RateLimitError`, `ProviderError`, etc.
- **Full type hints.** PEP 561 compliant.

## Authentication

Set your API key (required for most endpoints):

```bash
export VISGATE_API_KEY="vg-..."
```

Or pass directly:

```python
client = Client(api_key="vg-...")
```

## BYOK (Bring Your Own Key)

Use your own provider keys while routing through visgate:

```python
client = Client(
    fal_key="fal_...",
    replicate_key="r8_...",
    runway_key="rw_...",
)
```

## API Reference

### Image Generation

```python
# Quick generation
result = client.generate("a cat in space", model="fal-ai/flux/schnell")

# Full control
result = client.images.generate(
    model="fal-ai/flux/schnell",
    prompt="a cat in space",
    width=1024,
    height=1024,
    num_images=1,
)
```

### Video Generation

```python
result = client.videos.generate(
    model="fal-ai/flux-pro/video",
    prompt="Cinematic drone over Istanbul at golden hour, Bosphorus and minarets",
    duration_seconds=5.0,
)
print(result.video_url)
```

### Model Discovery

```python
models = client.models.list(provider="fal", media_type="image", limit=20)
for m in models.models:
    print(m.id, m.name)

model = client.models.get("fal-ai/flux/schnell")
```

### Usage and Billing

```python
usage = client.usage.get(period="month")
print(f"Requests: {usage.total_requests}, Cost: ${usage.total_billed_cost:.4f}")

logs = client.usage.logs(limit=50)
dashboard = client.usage.dashboard(period="week")
```

### Provider Management

```python
keys = client.providers.list_keys()
balances = client.providers.balances()
```

### Health Check

```python
health = client.health()
print(health["status"])  # "ok"
```

### Cache

The API caches by content (model + prompt + size). Repeat the same request to get a cache hit (`result.cache_hit == True`, lower latency and cost). See `examples/07_cache_demo.py`.

## Async Client

```python
from visgate_sdk import AsyncClient
import asyncio

async def main():
    async with AsyncClient() as client:
        result = await client.generate("a sunset")
        models = await client.models.list(limit=10)

asyncio.run(main())
```

## Error Handling

```python
from visgate_sdk import Client
from visgate_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    ProviderError,
    ValidationError,
    TimeoutError,
    VisgateError,
)

with Client() as client:
    try:
        result = client.generate("a sunset")
    except AuthenticationError:
        print("Check your API key")
    except RateLimitError as e:
        print(f"Slow down. Retry after {e.retry_after}s")
    except ProviderError as e:
        print(f"Provider {e.provider} failed: {e.message}")
    except TimeoutError:
        print("Request timed out")
    except VisgateError as e:
        print(f"API error [{e.error_code}]: {e.message}")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `$VISGATE_API_KEY` | visgate API key |
| `base_url` | `https://visgateai.com/api/v1` | API base URL |
| `timeout` | `120.0` | Request timeout (seconds) |
| `max_retries` | `2` | Automatic retries for transient errors |
| `fal_key` | `None` | Fal.ai BYOK key |
| `replicate_key` | `None` | Replicate BYOK key |
| `runway_key` | `None` | Runway BYOK key |

## Security & data

All API traffic uses HTTPS. Provider API keys (BYOK) are encrypted at rest; other account and usage data is stored on Google Cloud with encryption at rest. See the [API docs](docs/API.md) for more.

## Examples

Run image and video generation across **Fal, Replicate, and Runway** through one API. Each script is self-contained. Run in order: 00_smoke → 01_live → 00_auth → 01_models → … → 14_live_regression (simple to complex).

### Sample results (live API)

Real output from the examples against the deployed API.

**Health and auth**

```
OK /health: status=ok, version=0.2.0
OK /models: 5 models returned (limit=5), total=1704
auth_ok=true
organization_id=...
role=api-key
```

**Provider balances (Fal, Replicate, Runway)**

```
provider_balance_items=3
fal: configured=True available=True remaining=None limit=None currency=credits
replicate: configured=True available=True remaining=None limit=None currency=usd
runway: configured=True available=True remaining=1880.0 limit=10000.0 currency=credits
```

**Usage and billing**

```
usage_total_requests=257
usage_total_billed_cost=0.13
dashboard_total_cost_usd=0.13
```

**Generated images (3 providers — same prompt, different backends)**

Prompt: *"A cinematic view of Istanbul Bosphorus, detailed, photorealistic"*

| [Fal](examples/sample_outputs/sunset_istanbul.jpg) | [Replicate](examples/sample_outputs/galata_tower.jpg) | [Runway](examples/sample_outputs/bosphorus_night.jpg) |
|:---:|:---:|:---:|
| ![Fal](examples/sample_outputs/sunset_istanbul.jpg) | ![Replicate](examples/sample_outputs/galata_tower.jpg) | ![Runway](examples/sample_outputs/bosphorus_night.jpg) |

**Unified generate and cache**

| [generate_unified](examples/sample_outputs/generate_unified.jpg) | [cache_demo](examples/sample_outputs/cache_demo.jpg) (2nd request = cache hit) |
|:---:|:---:|
| ![unified](examples/sample_outputs/generate_unified.jpg) | ![cache](examples/sample_outputs/cache_demo.jpg) |

**Semantic cache (similar prompts)**

| [semantic_exact](examples/sample_outputs/semantic_exact.jpg) | [semantic_similar](examples/sample_outputs/semantic_similar.jpg) |
|:---:|:---:|
| ![exact](examples/sample_outputs/semantic_exact.jpg) | ![similar](examples/sample_outputs/semantic_similar.jpg) |

**Video (Veo from catalog)** — [istanbul.mp4](examples/sample_outputs/istanbul.mp4)

### Setup

```bash
# Create and activate venv (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# From project root: install SDK (editable for local dev)
pip install -e .

# Or from PyPI:
# pip install visgate-sdk

# Required for auth-dependent examples (from 00_auth_identity onward)
export VISGATE_API_KEY="vg-..."

# Optional: BYOK keys (for step 09 validate; steps 02, 03, 04)
export VISGATE_FAL_API_KEY="..."
export VISGATE_REPLICATE_API_KEY="..."
export VISGATE_RUNWAY_API_KEY="..."
```

### Running with a credentials file

If you keep your keys in a file (e.g. `.env` in the project root, or any path set in `VISGATE_ENV_FILE`), use the runner so all examples get the right env:

```bash
# From project root: load .env and run all examples
python examples/run_with_env.py

# Run a single example
python examples/run_with_env.py 04_videos_all_providers.py
```

The runner parses `KEY=value` lines (skips empty and `#` comments) and sets `os.environ` before running. Default file is repo root `.env`; override with `VISGATE_ENV_FILE=/path/to/file`.

### Run all steps

```bash
VISGATE_API_KEY=vg-... python3 examples/run_all_capabilities.py
```

Steps `00_smoke_sdk` and `01_live_api_smoke` run without an API key. From `00_auth_identity` onward, `VISGATE_API_KEY` is required.

Each script writes stdout to `examples/sample_outputs/out_<script>.txt` and downloads images/videos to `examples/sample_outputs/` when applicable.

**Low-cost run (no generation):** To verify the API without incurring cost, run only the non-generation steps: `00_smoke_sdk`, `01_live_api_smoke`, `00_auth_identity`, `01_models_catalog`, `05_usage_history_verify`, `06_provider_balances`, `09_provider_keys`, `10_api_keys`, `11_billing_readonly`. Generation steps (02, 03, 04, 07, 08, 12, 13, 14) call image/video APIs and consume credits.

```bash
# From project root (with .venv and .env): run cheap-only steps
for s in 00_smoke_sdk 01_live_api_smoke 00_auth_identity 01_models_catalog 05_usage_history_verify 06_provider_balances 09_provider_keys 10_api_keys 11_billing_readonly; do .venv/bin/python examples/run_with_env.py ${s}.py; done
```

### Step-by-step examples

| Step | Purpose | Command | Output |
|------|---------|--------|--------|
| 00_smoke_sdk | SDK version and resources (no network) | `python3 examples/00_smoke_sdk.py` | [out_00_smoke_sdk.txt](examples/sample_outputs/out_00_smoke_sdk.txt) |
| 01_live_api_smoke | Health + models (no auth) | `python3 examples/01_live_api_smoke.py` | [out_01_live_api_smoke.txt](examples/sample_outputs/out_01_live_api_smoke.txt) |
| 00_auth_identity | Auth /auth/me | `python3 examples/00_auth_identity.py` | [out_00_auth_identity.txt](examples/sample_outputs/out_00_auth_identity.txt) |
| 01_models_catalog | List, search, get models | `python3 examples/01_models_catalog.py` | [out_01_models_catalog.txt](examples/sample_outputs/out_01_models_catalog.txt) |
| 02_generate_unified | Unified generate (managed + BYOK) | `python3 examples/02_generate_unified.py` | [out_02_generate_unified.txt](examples/sample_outputs/out_02_generate_unified.txt) · [generate_unified.jpg](examples/sample_outputs/generate_unified.jpg) |
| 03_images_all_providers | Images: Fal, Replicate, Runway | `python3 examples/03_images_all_providers.py` | [out_03_images_all_providers.txt](examples/sample_outputs/out_03_images_all_providers.txt) · [sunset_istanbul.jpg](examples/sample_outputs/sunset_istanbul.jpg) [galata_tower.jpg](examples/sample_outputs/galata_tower.jpg) [bosphorus_night.jpg](examples/sample_outputs/bosphorus_night.jpg) |
| 04_videos_all_providers | Videos: all providers | `python3 examples/04_videos_all_providers.py` | [out_04_videos_all_providers.txt](examples/sample_outputs/out_04_videos_all_providers.txt) · [04_videos_sample.mp4](examples/sample_outputs/04_videos_sample.mp4) |
| 05_usage_history_verify | Usage, logs, dashboard | `python3 examples/05_usage_history_verify.py` | [out_05_usage_history_verify.txt](examples/sample_outputs/out_05_usage_history_verify.txt) |
| 06_provider_balances | Provider limits and balances | `python3 examples/06_provider_balances.py` | [out_06_provider_balances.txt](examples/sample_outputs/out_06_provider_balances.txt) |
| 07_cache_demo | Exact cache (identical requests) | `python3 examples/07_cache_demo.py` | [out_07_cache_demo.txt](examples/sample_outputs/out_07_cache_demo.txt) · [cache_demo.jpg](examples/sample_outputs/cache_demo.jpg) |
| 08_semantic_cache_demo | Semantic cache (similar prompts) | `python3 examples/08_semantic_cache_demo.py` | [out_08_semantic_cache_demo.txt](examples/sample_outputs/out_08_semantic_cache_demo.txt) · [semantic_exact.jpg](examples/sample_outputs/semantic_exact.jpg) [semantic_similar.jpg](examples/sample_outputs/semantic_similar.jpg) |
| 09_provider_keys | List and validate BYOK keys | `python3 examples/09_provider_keys.py` | [out_09_provider_keys.txt](examples/sample_outputs/out_09_provider_keys.txt) |
| 10_api_keys | List API keys | `python3 examples/10_api_keys.py` | [out_10_api_keys.txt](examples/sample_outputs/out_10_api_keys.txt) |
| 11_billing_readonly | Billing stats, info, pricing | `python3 examples/11_billing_readonly.py` | [out_11_billing_readonly.txt](examples/sample_outputs/out_11_billing_readonly.txt) |
| 12_veo_from_catalog | Veo from catalog → generate → write | `python3 examples/12_veo_from_catalog.py` | [out_12_veo_from_catalog.txt](examples/sample_outputs/out_12_veo_from_catalog.txt) · [istanbul.mp4](examples/sample_outputs/istanbul.mp4) |
| 13_async_generation | Async 202 + poll | `python3 examples/13_async_generation.py` | [out_13_async_generation.txt](examples/sample_outputs/out_13_async_generation.txt) |
| 14_live_regression_smoke | Managed mode + exact cache + semantic + async image/video (assertive smoke) | `python3 examples/14_live_regression_smoke.py` | [out_14_live_regression_smoke.txt](examples/sample_outputs/out_14_live_regression_smoke.txt) |

Full stdout for each step is in `examples/sample_outputs/out_<script>.txt`. All generated assets live in `examples/sample_outputs/`.

### Cache behavior

- **Exact cache (07):** Same model + prompt + size. Second request returns from cache; `cache_hit=True`.
- **Semantic cache (08):** Similar wording; API may match via embedding + Firestore.

### Out of scope

Auth signup/login, billing checkout/subscription/webhook, incoming webhooks, and streaming (SSE/WebSocket) are not covered; see [API docs](docs/API.md) for advanced use.

Quick reference and local run notes: [examples/README.md](examples/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT -- see [LICENSE](LICENSE).
