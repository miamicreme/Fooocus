from __future__ import annotations

from pathlib import Path


def test_one_ui_launcher_routes_through_engine_wait_script() -> None:
    content = Path("RUN_STUDIO_ONE_UI.bat").read_text(encoding="utf-8")
    normalized = content.replace("/", "\\")

    assert r"scripts\run_studio_one_ui.ps1" in normalized
    assert "engine wait" in content.lower()


def test_engine_wait_script_waits_for_ports_before_opening() -> None:
    content = Path("scripts/run_studio_one_ui.ps1").read_text(encoding="utf-8")

    assert "EngineWaitSeconds" in content
    assert "InitialEngineDelaySeconds" in content
    assert "Wait-PortOpen" in content
    assert "127.0.0.1:7872" in content
    assert "7865" in content


def test_engine_wait_script_uses_separate_stdout_and_stderr_logs() -> None:
    content = Path("scripts/run_studio_one_ui.ps1").read_text(encoding="utf-8")

    assert "RedirectStandardOutput $EngineOutLog" in content
    assert "RedirectStandardError $EngineErrLog" in content
    assert "RedirectStandardOutput $StudioOutLog" in content
    assert "RedirectStandardError $StudioErrLog" in content
