#!/usr/bin/env python3
"""Live API smoke test: health check and model listing (no auth required)."""
import sys
from contextlib import contextmanager
from pathlib import Path

from visgate_sdk import Client


@contextmanager
def _tee_stdout():
    out_dir = Path(__file__).resolve().parent / "sample_outputs"
    out_dir.mkdir(exist_ok=True)
    f = open(out_dir / f"out_{Path(__file__).stem}.txt", "w")
    old = sys.stdout
    class Tee:
        def write(self, s):
            old.write(s)
            f.write(s)
        def flush(self):
            old.flush()
            f.flush()
    sys.stdout = Tee()
    try:
        yield
    finally:
        sys.stdout = old
        f.close()


def main() -> int:
    with _tee_stdout():
        client = Client(api_key="not-used")
        try:
            health = client.health()
            assert health.get("status") == "ok", f"Unexpected health: {health}"
            print(f"OK /health: status={health['status']}, version={health.get('version')}")

            models = client.models.list(limit=5)
            count = len(models.models) if models.models else 0
            print(f"OK /models: {count} models returned (limit=5), total={models.total_count}")
        except Exception as e:
            print(f"FAIL: {e}")
            return 1
        finally:
            client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
