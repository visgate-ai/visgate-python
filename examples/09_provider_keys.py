"""
Step 11: Provider key list and validate (BYOK). Tested against live API.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from visgate_sdk import Client


def _pk(p: str) -> str | None:
    m = {"fal": ("VISGATE_FAL_API_KEY", "FAL_KEY"), "replicate": ("VISGATE_REPLICATE_API_KEY", "REPLICATE_API_KEY"), "runway": ("VISGATE_RUNWAY_API_KEY", "RUNWAY_API_KEY")}
    for var in m.get(p, ()):
        v = os.getenv(var, "").strip()
        if v:
            return v
    return None


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
    return Client(base_url=base_url, fal_key=_pk("fal"), replicate_key=_pk("replicate"), runway_key=_pk("runway"))


def main() -> None:
    with _tee_stdout():
        with _create_client() as client:
            keys_resp = client.providers.list_keys()
            print(f"provider_keys_count={len(keys_resp.keys)}")
            for k in keys_resp.keys:
                print(
                    f"  {k.provider}: validated={k.validated} "
                    f"validated_at={k.validated_at or '-'} masked={k.masked_key or '-'}"
                )

            for provider in ("fal", "replicate", "runway"):
                key = _pk(provider)
                if not key:
                    print(f"validate_skipped_{provider}=no_env_key")
                    continue
                result = client.providers.validate_key(provider, key)
                print(f"validate_{provider}=valid={result.valid} message={result.message}")


if __name__ == "__main__":
    main()
