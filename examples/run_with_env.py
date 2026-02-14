"""
Run examples with environment variables loaded from an env file (default: .env in project root, or VISGATE_ENV_FILE).
Usage:
  python examples/run_with_env.py
  python examples/run_with_env.py 04_videos_all_providers.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        print(f"Env file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key:
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"'))
                    or (value.startswith("'") and value.endswith("'"))
                ):
                    value = value[1:-1]
                os.environ[key] = value


def main() -> None:
    env_file = os.environ.get("VISGATE_ENV_FILE")
    if env_file:
        path = Path(env_file)
    else:
        path = Path(__file__).resolve().parent.parent / ".env"
    _load_env_file(path)

    base_dir = Path(__file__).resolve().parent
    if len(sys.argv) > 1:
        script = sys.argv[1]
        if not script.endswith(".py"):
            script = f"{script}.py"
        script_path = base_dir / script
        if not script_path.is_file():
            print(f"Script not found: {script_path}", file=sys.stderr)
            sys.exit(1)
        import subprocess
        sys.exit(subprocess.run([sys.executable, str(script_path)], env=os.environ).returncode)

    import run_all_capabilities
    run_all_capabilities.main()


if __name__ == "__main__":
    main()
