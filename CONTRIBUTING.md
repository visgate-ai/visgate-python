# Contributing to visgate-sdk

Thanks for your interest in contributing.

## Setup

```bash
git clone https://github.com/visgate-ai/visgate-python.git
cd visgate-python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development

```bash
# Lint
ruff check src/ tests/ examples/

# Unit tests
pytest tests/ -v

# Smoke test (no network)
python examples/00_smoke_sdk.py

# Live API smoke test (no auth needed)
python examples/01_live_api_smoke.py
```

## Pull Requests

1. Fork the repo and create a feature branch.
2. Make your changes. Add tests for new functionality.
3. Ensure `ruff check src/ tests/ examples/` and `pytest tests/ -v` pass.
4. Open a PR with a clear description of what changed and why.

## Code Style

- Python 3.9+ compatible.
- Use `from __future__ import annotations` in all modules.
- Run `ruff check src/ tests/ examples/` before committing.
- Keep the public API surface minimal.
- Every public export must be in `__init__.py` `__all__`.
- No multiple statements on one line (no semicolons); no f-strings without placeholders.
- User-facing strings in English only.

## Releasing

Version is single-sourced from `pyproject.toml`. To release:

1. Bump version in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Commit and push to `main`.
4. Create a GitHub Release with the tag (e.g. `v0.3.0`).
5. The PyPI publish workflow runs automatically.
