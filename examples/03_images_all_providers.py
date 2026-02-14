"""
Step 05: Prompt-to-image BYOK checks for Fal, Replicate, Runway. Tested against live API.
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
        prompt = "A cinematic view of Istanbul Bosphorus, detailed, photorealistic"
        providers = [
        ("fal", "fal-ai/flux/schnell"),
        ("replicate", "replicate/black-forest-labs/flux-schnell"),
            ("runway", "runway/gen4_image"),
        ]

        with _create_client() as client:
            for provider, model in providers:
                key = _pk(provider)
                if not key:
                    print(f"{provider}_image_skipped=true")
                    continue

                client.set_provider_headers(
                    fal_key=key if provider == "fal" else None,
                    replicate_key=key if provider == "replicate" else None,
                    runway_key=key if provider == "runway" else None,
                )
                result = client.images.generate(
                    model=model,
                    prompt=prompt,
                    width=1024,
                    height=1024,
                    num_images=1,
                )
                print(f"{provider}_image_id={result.id}")
                print(f"{provider}_image_provider={result.provider}")
                if result.images:
                    names = {"fal": "sunset_istanbul", "replicate": "galata_tower", "runway": "bosphorus_night"}
                    path = out_dir / f"{names.get(provider, provider)}.jpg"
                    r = httpx.get(result.images[0], follow_redirects=True)
                    path.write_bytes(r.content)


if __name__ == "__main__":
    main()
