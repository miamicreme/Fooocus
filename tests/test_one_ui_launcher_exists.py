from __future__ import annotations

from pathlib import Path


def test_one_ui_launcher_routes_through_safe_studio_script() -> None:
    content = Path("RUN_STUDIO_ONE_UI.bat").read_text(encoding="utf-8")
    normalized = content.replace("/", "\\")

    assert r"scripts\run_studio_one_ui.ps1" in normalized
    assert "Engine auto-start is OFF" in content
    assert "-StartEngine" not in content


def test_optional_engine_launcher_exists() -> None:
    content = Path("RUN_STUDIO_WITH_ENGINE.bat").read_text(encoding="utf-8")
    normalized = content.replace("/", "\\")

    assert r"scripts\run_studio_one_ui.ps1" in normalized
    assert "-StartEngine" in content


def test_manual_fooocus_engine_launcher_exists() -> None:
    content = Path("RUN_FOOOCUS_ENGINE_ONLY.bat").read_text(encoding="utf-8")

    assert "launch.py --disable-analytics --disable-in-browser" in content
    assert "stable command" in content


def test_engine_wait_script_supports_optional_engine_and_no_duplicate_tabs() -> None:
    content = Path("scripts/run_studio_one_ui.ps1").read_text(encoding="utf-8")

    assert "[switch]$StartEngine" in content
    assert "Skipping Fooocus engine auto-start" in content
    assert "Not opening another browser tab" in content
    assert "startedStudio" in content
    assert "127.0.0.1:7872" in content


def test_engine_wait_script_uses_separate_stdout_and_stderr_logs() -> None:
    content = Path("scripts/run_studio_one_ui.ps1").read_text(encoding="utf-8")

    assert "RedirectStandardOutput $EngineOutLog" in content
    assert "RedirectStandardError $EngineErrLog" in content
    assert "RedirectStandardOutput $StudioOutLog" in content
    assert "RedirectStandardError $StudioErrLog" in content
