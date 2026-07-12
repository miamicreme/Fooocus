from __future__ import annotations

import inspect

import ai_studio_app
from ai_studio_app import build_app, fooocus_iframe_html


def test_designed_control_ui_hides_engine_and_adds_downloads() -> None:
    source = inspect.getsource(ai_studio_app.build_app)

    assert "Studio Control Center" in source
    assert "Hidden Fooocus engine" in source
    assert "open=False" in source
    assert "Download Prompt Pack" in source
    assert "Download Session History" in source
    assert "Generated image history" in source
    assert "Fooocus Engine" not in source.split("with gr.Tab(")[1]


def test_designed_control_ui_adds_safe_send_to_engine_handoff() -> None:
    source = inspect.getsource(ai_studio_app.build_app)

    assert "Send to Engine" in source
    assert "build_engine_handoff_text" in source
    assert "Engine-ready fields to paste into Fooocus" in source
    assert "Browser safety blocks direct auto-fill" in source


def test_fooocus_iframe_is_available_but_not_the_primary_ui() -> None:
    html = fooocus_iframe_html()

    assert "127.0.0.1:7865" in html
    assert "iframe" in html


def test_designed_control_ui_builds_without_launching() -> None:
    app = build_app()

    assert app is not None
