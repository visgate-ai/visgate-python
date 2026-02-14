"""
Step 06: Video checks (managed + BYOK providers). Tested against live API.
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
        prompt = "Short cinematic drone shot over Istanbul at golden hour"

        with _create_client() as client:
            client.set_provider_headers()
            managed = client.videos.generate(
                model="fal-ai/veo3",
                prompt=prompt,
                duration_seconds=6.0,
                skip_gcs_upload=True,
            )
            print(f"managed_video_id={managed.id}")
            if getattr(managed, "video_url", None):
                r = httpx.get(managed.video_url, follow_redirects=True)
                (out_dir / "04_videos_sample.mp4").write_bytes(r.content)

            fal = _pk("fal")
            if fal:
                client.set_provider_headers(fal_key=fal)
                result = client.videos.generate(
                    model="fal-ai/veo3",
                    prompt=prompt,
                    duration_seconds=6.0,
                    skip_gcs_upload=True,
                )
                print(f"fal_video_id={result.id}")
            else:
                print("fal_video_skipped=true")

            replicate = _pk("replicate")
            if replicate:
                client.set_provider_headers(replicate_key=replicate)
                result = client.videos.generate(
                    model="replicate/lucataco/cogvideox-5b",
                    prompt=prompt,
                    duration_seconds=5.0,
                    skip_gcs_upload=True,
                )
                print(f"replicate_video_id={result.id}")
            else:
                print("replicate_video_skipped=true")

            runway = _pk("runway")
            if runway:
                client.set_provider_headers(runway_key=runway)
                result = client.videos.generate(
                    model="runway/gen4_turbo",
                    prompt=prompt,
                    duration_seconds=5.0,
                    skip_gcs_upload=True,
                )
                print(f"runway_video_id={result.id}")
            else:
                print("runway_video_skipped=true")


if __name__ == "__main__":
    main()
