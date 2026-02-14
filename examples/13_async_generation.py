"""
Step 15: Async generation (202 + poll) for video and image.
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
            print("  Async video (wait=False)...")
            req = client.videos.generate(
                model="fal-ai/veo3",
                prompt="Short drone shot over Istanbul at golden hour",
                duration_seconds=4.0,
                skip_gcs_upload=True,
                wait=False,
            )
            if hasattr(req, "request_id"):
                print(f"  request_id={req.request_id}")
                result = req.wait(timeout=180, poll_interval=3)
                print(f"  status={result.status} output_url={result.output_url}")
            else:
                print(f"  Sync response (wait=True fallback): id={req.id}")

            print("  Async image (wait=False)...")
            req = client.images.generate(
                model="fal-ai/flux/schnell",
                prompt="A sunset over the Bosphorus",
                wait=False,
            )
            if hasattr(req, "request_id"):
                print(f"  request_id={req.request_id}")
                result = req.wait(timeout=60, poll_interval=2)
                print(f"  status={result.status} output_url={result.output_url}")
            else:
                print(f"  Sync response (wait=True fallback): id={req.id}")

        print("  async_generation_done=true")


if __name__ == "__main__":
    main()
