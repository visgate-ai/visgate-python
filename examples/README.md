# SDK examples — quick reference

Full examples guide, sample results gallery, step-by-step table, setup, and low-cost run are in the [main README (Examples section)](../README.md#examples).

## Run from project root

```bash
# With API key in environment
VISGATE_API_KEY=vg-... python3 examples/run_all_capabilities.py

# With credentials file (e.g. .env in repo root)
python examples/run_with_env.py
python examples/run_with_env.py 04_videos_all_providers.py   # single example
```

Override env file path with `VISGATE_ENV_FILE=/path/to/file`. Default file is repo root `.env`.
