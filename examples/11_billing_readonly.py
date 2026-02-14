"""
Step 13: Billing read-only (stats, info, pricing). Tested against live API.
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
            stats = client._request("GET", "/billing/stats")
            print("billing_stats_keys=" + ",".join(sorted(stats.keys())) if isinstance(stats, dict) else "billing_stats=non_dict")

            info = client._request("GET", "/billing/info")
            if isinstance(info, dict):
                print("billing_info_keys=" + ",".join(sorted(k for k in info.keys() if not k.startswith("_"))))
            else:
                print("billing_info=ok" if info is not None else "billing_info=null")

            pricing = client._request("GET", "/billing/pricing")
            if isinstance(pricing, dict):
                print("billing_pricing_keys=" + ",".join(sorted(pricing.keys())))
            else:
                print("billing_pricing=ok" if pricing is not None else "billing_pricing=null")


if __name__ == "__main__":
    main()
