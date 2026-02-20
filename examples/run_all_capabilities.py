"""
Run all SDK capability examples in order. All examples are tested against the live API.
Default: https://visgateai.com/api/v1 (override with VISGATE_BASE_URL).
VISGATE_API_KEY is required for auth-dependent steps.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPTS = [
    "00_smoke_sdk.py",          # no network
    "01_live_api_smoke.py",     # health + models, no auth
    "00_auth_identity.py",      # auth /auth/me
    "01_models_catalog.py",     # list, search, get
    "02_generate_unified.py",   # unified generate (managed + BYOK)
    "03_images_all_providers.py",
    "04_videos_all_providers.py",
    "05_usage_history_verify.py",
    "06_provider_balances.py",
    "07_cache_demo.py",         # exact cache
    "08_semantic_cache_demo.py", # semantic cache
    "09_provider_keys.py",
    "10_api_keys.py",
    "11_billing_readonly.py",
    "12_veo_from_catalog.py",
    "13_async_generation.py",   # 202 + poll
    "14_live_regression_smoke.py",  # managed mode + cache + semantic + async end-to-end
]


def main() -> None:
    base_dir = Path(__file__).parent
    failed = False

    for script in SCRIPTS:
        script_path = base_dir / script
        print(f"\n=== RUN {script} ===")
        completed = subprocess.run([sys.executable, str(script_path)], check=False)
        if completed.returncode != 0:
            failed = True
            print(f"step_failed={script}")
            break

    if failed:
        raise SystemExit(1)

    print("\nall_steps_completed=true")


if __name__ == "__main__":
    main()
