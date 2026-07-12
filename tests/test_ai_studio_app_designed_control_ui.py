from __future__ import annotations

import inspect

import ai_studio_app
from ai_studio_app import build_app


def test_designed_control_ui_keeps_studio_primary_and_engine_separate() -> None:
    source = inspect.getsource(ai_studio_app.build_app)

    assert "Studio Control Center" in source
    assert "Engine status" in source
    assert "open=False" in source
    assert "Download Prompt Pack" in source
    assert "Download Session History" in source
    assert "Generated image history" in source
    assert "RUN_FOOOCUS_ENGINE_ONLY.bat" in source
    assert "iframe" not in source


def test_designed_control_ui_builds_without_launching() -> None:
    app = build_app()

    assert app is not None
