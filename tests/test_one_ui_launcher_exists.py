from __future__ import annotations

from pathlib import Path


def test_one_ui_launcher_exists_and_points_to_single_ui() -> None:
    content = Path("RUN_STUDIO_ONE_UI.bat").read_text(encoding="utf-8")

    assert "ai_studio_app.py" in content
    assert "scripts\run_fooocus_keepalive.py" in content
    assert "http://127.0.0.1:7872" in content


def test_new_launcher_menu_exposes_start_refresh_hot_and_cold_reset() -> None:
    content = Path("START_AI_IMAGE_STUDIO.bat").read_text(encoding="utf-8")

    assert "AI Image Studio Launcher" in content
    assert "Start / Open AI Image Studio" in content
    assert "Refresh browser only" in content
    assert "Hot reset Studio only" in content
    assert "Cold reset Studio + Fooocus engine" in content
    assert "scripts\studio_reset.ps1" in content


def test_direct_reset_shortcuts_call_reset_helper() -> None:
    hot = Path("HOT_RESET_STUDIO.bat").read_text(encoding="utf-8")
    cold = Path("COLD_RESET_STUDIO.bat").read_text(encoding="utf-8")
    refresh = Path("REFRESH_AI_STUDIO.bat").read_text(encoding="utf-8")

    assert "-Mode hot" in hot
    assert "-Mode cold" in cold
    assert "-Mode refresh" in refresh


def test_reset_helper_supports_logs_and_port_restart_modes() -> None:
    content = Path("scripts/studio_reset.ps1").read_text(encoding="utf-8")

    assert "logs\studio" in content
    assert "latest-ai-studio.log" in content
    assert "latest-fooocus-engine.log" in content
    assert "Start-LoggedWindow" in content
    assert "Stop-PortProcess 7872" in content
    assert "Stop-PortProcess 7865" in content


def test_logged_process_runner_keeps_exact_crash_logs() -> None:
    content = Path("scripts/run_logged_process.ps1").read_text(encoding="utf-8")

    assert "Exact log saved to" in content
    assert "Latest log shortcut" in content
    assert "exited with code" in content
    assert "stack trace above" in content
