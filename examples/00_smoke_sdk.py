#!/usr/bin/env python3
"""Smoke test: version and client instantiation (no network required)."""
import sys
from contextlib import contextmanager
from pathlib import Path

from visgate_sdk import Client, __version__


@contextmanager
def _tee_stdout():
    out_dir = Path(__file__).resolve().parent / "sample_outputs"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"out_{Path(__file__).stem}.txt"
    f = open(out, "w")
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


def main() -> int:
    with _tee_stdout():
        assert __version__, f"Version should not be empty, got: {__version__!r}"

        client = Client(api_key="placeholder", base_url="https://visgateai.com/api/v1")
        assert client.images is not None
        assert client.models is not None
        assert client.videos is not None
        assert client.requests is not None
        assert client.usage is not None
        assert client.providers is not None
        assert callable(client.generate)
        assert callable(client.health)
        client.close()

        print(f"OK: visgate-sdk v{__version__}, all resources (images, models, videos, requests, usage, providers) initialized")
    return 0


if __name__ == "__main__":
    sys.exit(main())
