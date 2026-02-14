"""
Step 08: Fetch provider limits/remaining balances from VisGate. Tested against live API.
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
            balances = client.providers.balances().balances
            print(f"provider_balance_items={len(balances)}")
            for item in balances:
                provider = item.provider
                configured = item.configured
                available = item.available
                remaining = item.remaining
                limit_value = item.limit
                currency = item.currency
                print(
                    f"{provider}: configured={configured} available={available} "
                    f"remaining={remaining} limit={limit_value} currency={currency}"
                )


if __name__ == "__main__":
    main()
