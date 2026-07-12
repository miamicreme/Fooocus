from __future__ import annotations

import runpy
import time
from pathlib import Path


def is_gradio_startup_probe_timeout(exc: Exception) -> bool:
    """Return True when Gradio started but its local URL probe timed out.

    Gradio 3.x can raise a requests ReadTimeout from networking.url_ok()
    after printing the local URL. In that case the server thread may already
    be running, so the launcher should keep the process alive instead of
    closing the command window.
    """
    text = f"{type(exc).__name__}: {exc}"
    return (
        "ReadTimeout" in text
        and "127.0.0.1" in text
        and "7865" in text
        and "timed out" in text.lower()
    )


def run_launch(launch_path: Path) -> None:
    try:
        runpy.run_path(str(launch_path), run_name="__main__")
    except SystemExit as exc:
        if exc.code in (None, 0):
            print("Fooocus launch requested a clean exit after starting Gradio. Keeping this process alive.")
            return
        raise
    except Exception as exc:
        if is_gradio_startup_probe_timeout(exc):
            print("Fooocus Gradio local URL probe timed out after the server started. Keeping this process alive.")
            print(f"Startup probe warning: {type(exc).__name__}: {exc}")
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
