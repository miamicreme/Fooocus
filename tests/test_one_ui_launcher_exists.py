from __future__ import annotations

from pathlib import Path


def test_one_ui_launcher_exists_and_points_to_single_ui() -> None:
    content = Path("RUN_STUDIO_ONE_UI.bat").read_text(encoding="utf-8")

    assert "ai_studio_app.py" in content
    assert "launch.py --disable-analytics" in content
    assert "http://127.0.0.1:7872" in content
