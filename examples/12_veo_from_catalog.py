"""
Step 14: Video with Veo from catalog (get models → filter → generate → write).
"""
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

OUTPUT_DIR = Path(__file__).resolve().parent / "sample_outputs"
OUTPUT_VIDEO = OUTPUT_DIR / "istanbul.mp4"
PROMPT = "Cinematic drone over Istanbul at golden hour, Bosphorus and minarets, 4k"
DURATION = 6.0
FALLBACK_MODEL = "fal-ai/veo3"


def pick_newest_veo(models_response):
    """Filter models containing 'veo' in id/name, sort by first_seen_at (newest first), return first."""
    veo = [
        m
        for m in models_response.models
        if m
        and ("veo" in (m.id or "").lower() or "veo" in (m.name or "").lower())
    ]
    if not veo:
        return None
    # Newest first (first_seen_at desc; None last)
    veo.sort(key=lambda m: m.first_seen_at or "", reverse=True)
    return veo[0].id


def download_url(url: str, path: Path, timeout: float = 120.0) -> None:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)


def main() -> None:
    with _tee_stdout():
        client = _create_client()

        # 1. Get video models from API (database), newest first
        resp = client.models.list(
            provider="fal",
            model_type="video",
            sort="newest",
            limit=100,
        )
        model_id = pick_newest_veo(resp)
        if not model_id:
            model_id = FALLBACK_MODEL
            print(f"  No Veo in catalog; using fallback {model_id}")
        else:
            print(f"  Using newest Veo from catalog: {model_id}")

        print(f"  Generating video (prompt={PROMPT[:50]}...) ...")
        result = client.videos.generate(
            model=model_id,
            prompt=PROMPT,
            duration_seconds=6.0,
            skip_gcs_upload=True,
        )
        if not result.video_url:
            print("  No video_url in response.")
            return
        print("  Got video_url")

        download_url(result.video_url, OUTPUT_VIDEO)
        print(f"  Written {OUTPUT_VIDEO}")
        client.close()


if __name__ == "__main__":
    main()
