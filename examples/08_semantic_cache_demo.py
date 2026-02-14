#!/usr/bin/env python3
"""Step 10: Semantic cache demo — similar prompts may hit semantic cache."""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

import httpx

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


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "sample_outputs"
    with _tee_stdout():
        prompt1 = "Istanbul Bosphorus at golden hour, minarets visible, cinematic"
        prompt2 = "Bosphorus Istanbul golden hour with minarets, cinematic"
        model = "fal-ai/flux/schnell"
        width, height = 1024, 1024

        with _create_client() as client:
            r1 = client.images.generate(
                model=model,
                prompt=prompt1,
                width=width,
                height=height,
                num_images=1,
                include_steps=True,
            )
            print(f"Request 1 (exact): cache_hit={r1.cache_hit}, latency_ms={r1.latency_ms}, cost={r1.cost}")
            if r1.images:
                r = httpx.get(r1.images[0], follow_redirects=True)
                (out_dir / "semantic_exact.jpg").write_bytes(r.content)

            r2 = client.images.generate(
                model=model,
                prompt=prompt2,
                width=width,
                height=height,
                num_images=1,
                include_steps=True,
            )
            print(
                f"Request 2 (similar): cache_hit={r2.cache_hit}, latency_ms={r2.latency_ms}, cost={r2.cost}, "
                f"provider_cost_avoided_micro={r2.provider_cost_avoided_micro}"
            )
            if r2.images:
                r = httpx.get(r2.images[0], follow_redirects=True)
                (out_dir / "semantic_similar.jpg").write_bytes(r.content)

            if r2.cache_hit:
                print("OK: Second request was cache hit (semantic match). Cost avoided vs provider.")
            else:
                print("Note: Second request was not a cache hit (semantic search may need embeddings/Vertex AI enabled).")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
