from __future__ import annotations

from pathlib import Path


def test_engine_only_launcher_uses_direct_launch() -> None:
    content = Path("RUN_FOOOCUS_ENGINE_ONLY.bat").read_text(encoding="utf-8")

    assert "launch.py" in content
    assert "scripts\\run_fooocus_keepalive.py" not in content
    assert "--disable-in-browser" in content


def test_cpu_safe_engine_launcher_avoids_cuda() -> None:
    content = Path("RUN_FOOOCUS_CPU_SAFE.bat").read_text(encoding="utf-8")

    assert "launch.py" in content
    assert "scripts\\run_fooocus_keepalive.py" not in content
    assert "--always-cpu 4" in content
    assert "--disable-in-browser" in content
    assert "--attention-pytorch" in content


def test_low_vram_safe_engine_launcher_uses_conservative_cuda_flags() -> None:
    content = Path("RUN_FOOOCUS_LOWVRAM_SAFE.bat").read_text(encoding="utf-8")

    assert "launch.py" in content
    assert "scripts\\run_fooocus_keepalive.py" not in content
    assert "--always-no-vram" in content
    assert "--vae-in-cpu" in content
    assert "--disable-async-cuda-allocation" in content
