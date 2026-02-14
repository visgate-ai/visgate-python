"""
Step 12: List API keys (GET /api-keys). Tested against live API.
"""
from __future__ import annotations

import os
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


def _create_client() -> Client:
    base_url = os.getenv("VISGATE_BASE_URL", "https://visgateai.com/api/v1").strip()
    def _pk(p: str) -> str | None:
        m = {"fal": ("VISGATE_FAL_API_KEY", "FAL_KEY"), "replicate": ("VISGATE_REPLICATE_API_KEY", "REPLICATE_API_KEY"), "runway": ("VISGATE_RUNWAY_API_KEY", "RUNWAY_API_KEY")}
        for var in m.get(p, ()):
            v = os.getenv(var, "").strip()
            if v:
                return v
        return None
    return Client(base_url=base_url, fal_key=_pk("fal"), replicate_key=_pk("replicate"), runway_key=_pk("runway"))


def main() -> None:
    with _tee_stdout():
        with _create_client() as client:
            data = client._request("GET", "/api-keys")
            keys = data if isinstance(data, list) else []
            print(f"api_keys_count={len(keys)}")
            for item in keys:
                kid = item.get("id", "")
                name = item.get("name", "")
                prefix = item.get("key_prefix", "")
                print(f"  id={kid} name={name} key_prefix={prefix}")


if __name__ == "__main__":
    main()
