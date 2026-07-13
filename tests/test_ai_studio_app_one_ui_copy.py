from __future__ import annotations

import inspect

import ai_studio_app
from ai_studio_app import build_app, copyable_textbox


def test_copyable_textbox_helper_enables_copy_button() -> None:
    source = inspect.getsource(copyable_textbox)

    assert "show_copy_button=True" in source


def test_ai_studio_app_uses_copy_controls_and_separate_engine_status() -> None:
    source = inspect.getsource(ai_studio_app.build_app)

    assert "Engine status" in source
    assert "Copy controls" in source or "copy buttons" in source
    assert "fallback/debugging" in source
    assert "copyable_textbox" in source
    assert "RUN_FOOOCUS_ENGINE_ONLY.bat" in source


def test_ai_studio_app_builds_one_ui_without_launching() -> None:
    app = build_app()

    assert app is not None
