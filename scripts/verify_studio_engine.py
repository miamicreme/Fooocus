from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from uuid import uuid4

ENGINE_URL = "http://127.0.0.1:7865"
HEALTH_API = "/studio_health"
GENERATE_API = "/studio_generate"
CANCEL_API = "/studio_cancel"


def _fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def _pass(message: str) -> None:
    print(f"[PASS] {message}")


def _client():
    try:
        from gradio_client import Client  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"gradio_client is not installed: {exc}") from exc
    return Client(ENGINE_URL)


def check_health(client) -> dict:
    response = client.predict(json.dumps({"check": "studio"}), api_name=HEALTH_API)
    if isinstance(response, str):
        response = json.loads(response)
    if not isinstance(response, dict):
        raise RuntimeError(f"Unexpected health response: {response!r}")
    if response.get("status") != "ok":
        raise RuntimeError(str(response.get("message") or response))
    apis = set(response.get("apis") or [])
    required = {HEALTH_API, GENERATE_API, CANCEL_API}
    missing = sorted(required - apis)
    if missing:
        raise RuntimeError(f"Health endpoint did not report required APIs: {missing}")
    return response


def smoke_generate(client) -> list[str]:
    payload = {
        "job_id": f"studio-smoke-{uuid4().hex}",
        "goal": "Studio smoke test",
        "prompt": "simple studio smoke test image, clean object photo, neutral background",
        "negative_prompt": "blurry, distorted, low quality",
        "workflow": "text_to_image",
        "references": [],
        "settings": {
            "performance": "Speed",
            "image_number": "1",
            "aspect_ratio": "1024x1024",
            "seed": -1,
        },
        "metadata": {"source": "verify_studio_engine"},
    }
    response = client.predict(json.dumps(payload), api_name=GENERATE_API)
    if isinstance(response, str):
        response = json.loads(response)
    if not isinstance(response, dict):
        raise RuntimeError(f"Unexpected generation response: {response!r}")
    if response.get("status") != "completed":
        raise RuntimeError(str(response.get("message") or response))
    output_paths = [str(path) for path in response.get("output_paths") or []]
    if not output_paths:
        raise RuntimeError("Generation completed but returned no output paths.")
    missing = [path for path in output_paths if not Path(path).exists()]
    if missing:
        raise RuntimeError(f"Generation returned missing file paths: {missing}")
    return output_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Studio-to-Fooocus engine contract.")
    parser.add_argument("--generate", action="store_true", help="Run one real text-to-image smoke generation.")
    args = parser.parse_args()

    print("Studio Engine Verification")
    print(f"Engine: {ENGINE_URL}")
    print("Checking stable endpoints...")
    try:
        client = _client()
        health = check_health(client)
        _pass(f"Health endpoint OK: {health.get('message')}")
        _pass(f"Required APIs reported: {', '.join(health.get('apis') or [])}")
    except Exception as exc:
        return _fail(str(exc))

    if args.generate:
        print("Running one real text-to-image smoke generation...")
        started = time.perf_counter()
        try:
            outputs = smoke_generate(client)
        except Exception as exc:
            return _fail(str(exc))
        elapsed = time.perf_counter() - started
        _pass(f"Generated {len(outputs)} output(s) in {elapsed:.1f}s")
        for output in outputs:
            print(f"  - {output}")
    else:
        print("[SKIP] Real generation not requested. Use the Generate Smoke option to test image creation.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
