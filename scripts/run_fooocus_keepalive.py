from __future__ import annotations

import runpy
import time
from pathlib import Path


def run_launch(launch_path: Path) -> None:
    try:
        runpy.run_path(str(launch_path), run_name="__main__")
    except SystemExit as exc:
        if exc.code in (None, 0):
            print("Fooocus launch requested a clean exit after starting Gradio. Keeping this process alive.")
            return
        raise


def keepalive_loop() -> None:
    print("Fooocus launch returned. Keeping this process alive so the local server stays reachable.")
    print("Keep this window open. Press Ctrl+C to stop Fooocus.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Fooocus keepalive stopped by user.")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    launch_path = repo_root / "launch.py"
    run_launch(launch_path)
    keepalive_loop()


if __name__ == "__main__":
    main()
