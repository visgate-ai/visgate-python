"""
Step 16: Live regression smoke — managed mode, exact cache, semantic cache, async image/video.
"""
from __future__ import annotations

import os
import sys
import time
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
    return Client(base_url=base_url)


def _assert(cond: bool, message: str) -> None:
    if not cond:
        print(f"FAIL: {message}")
        raise SystemExit(1)


def main() -> None:
    suffix = str(int(time.time()))
    with _tee_stdout():
        with _create_client() as client:
            print("check=managed_mode")
            managed = client.generate(
                prompt=f"Istanbul skyline golden hour regression {suffix}",
                model="fal-ai/flux/schnell",
            )
            print(f"managed_id={managed.id}")
            print(f"managed_mode={managed.mode}")
            _assert(managed.mode == "managed", "Unified generate must be managed without explicit BYOK header")

            print("check=exact_cache")
            prompt_exact = f"Bosphorus cinematic exact cache {suffix}"
            r1 = client.images.generate(
                model="fal-ai/flux/schnell",
                prompt=prompt_exact,
                width=1024,
                height=1024,
                num_images=1,
                include_steps=True,
            )
            r2 = client.images.generate(
                model="fal-ai/flux/schnell",
                prompt=prompt_exact,
                width=1024,
                height=1024,
                num_images=1,
                include_steps=True,
            )
            print(f"exact_first_cache_hit={r1.cache_hit}")
            print(f"exact_second_cache_hit={r2.cache_hit}")
            _assert(not r1.cache_hit and r2.cache_hit, "Exact cache should hit on second identical request")

            print("check=semantic_cache")
            p1 = f"Istanbul Bosphorus bridge at sunset cinematic {suffix}"
            p2 = f"Cinematic sunset over Bosphorus bridge Istanbul {suffix}"
            s1 = client.images.generate(
                model="fal-ai/flux/schnell",
                prompt=p1,
                width=1024,
                height=1024,
                num_images=1,
                include_steps=True,
            )
            print(f"semantic_first_cache_hit={s1.cache_hit}")

            semantic_hit = False
            for attempt in range(1, 4):
                s2 = client.images.generate(
                    model="fal-ai/flux/schnell",
                    prompt=p2,
                    width=1024,
                    height=1024,
                    num_images=1,
                    include_steps=True,
                )
                print(f"semantic_attempt_{attempt}_cache_hit={s2.cache_hit}")
                if s2.cache_hit:
                    semantic_hit = True
                    break
                time.sleep(5)
            _assert(semantic_hit, "Semantic cache should hit for similar prompt")

            print("check=async_image")
            async_img = client.images.generate(
                model="fal-ai/flux/schnell",
                prompt=f"Async image Istanbul sunset {suffix}",
                wait=False,
            )
            _assert(hasattr(async_img, "request_id"), "Async image should return request_id")
            img_result = async_img.wait(timeout=120, poll_interval=3)
            print(f"async_image_status={img_result.status}")
            print(f"async_image_output={img_result.output_url}")
            _assert(img_result.status == "completed" and bool(img_result.output_url), "Async image must complete with output URL")

            print("check=async_video")
            async_vid = client.videos.generate(
                model="fal-ai/veo3",
                prompt=f"Short drone over Istanbul Bosphorus {suffix}",
                duration_seconds=4.0,
                skip_gcs_upload=True,
                wait=False,
            )
            _assert(hasattr(async_vid, "request_id"), "Async video should return request_id")
            vid_result = async_vid.wait(timeout=300, poll_interval=4)
            print(f"async_video_status={vid_result.status}")
            print(f"async_video_output={vid_result.output_url}")
            _assert(vid_result.status == "completed" and bool(vid_result.output_url), "Async video must complete with output URL")

        print("live_regression_ok=true")


if __name__ == "__main__":
    main()
