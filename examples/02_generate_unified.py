"""
Step 04: Unified generate endpoint checks (managed + fal BYOK). Tested against live API.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

import httpx

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
    out_dir = Path(__file__).resolve().parent / "sample_outputs"
    with _tee_stdout():
        prompt = "Istanbul skyline at sunset, realistic photo"
        with _create_client() as client:
            client.set_provider_headers()
            managed = client.generate(prompt=prompt, model="fal-ai/flux/schnell")
            print(f"managed_generate_id={managed.id}")
            if managed.image_url:
                out_dir.mkdir(exist_ok=True)
                r = httpx.get(managed.image_url, follow_redirects=True)
                (out_dir / "generate_unified.jpg").write_bytes(r.content)
            print(f"managed_generate_mode={managed.mode}")

            fal = _pk("fal")
            if fal:
                client.set_provider_headers(fal_key=fal)
                byok = client.generate(prompt=prompt, model="fal-ai/flux/schnell")
                print(f"byok_generate_id={byok.id}")
                print(f"byok_generate_mode={byok.mode}")
            else:
                print("byok_generate_skipped=true")


if __name__ == "__main__":
    main()
