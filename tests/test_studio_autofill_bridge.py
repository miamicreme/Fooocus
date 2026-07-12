from __future__ import annotations

from pathlib import Path
import inspect

import modules.ui_gradio_extensions as ui_gradio_extensions


BRIDGE_PATH = Path("javascript/studio-autofill-bridge.js")


def test_fooocus_autofill_bridge_script_exists_and_listens_for_studio_message() -> None:
    source = BRIDGE_PATH.read_text(encoding="utf-8")

    assert "fooocus-studio-autofill" in source
    assert "window.addEventListener(\"message\"" in source
    assert "allowedOrigins" in source
    assert "127.0.0.1:7872" in source
    assert "localhost:7872" in source


def test_fooocus_autofill_bridge_targets_prompt_fields() -> None:
    source = BRIDGE_PATH.read_text(encoding="utf-8")

    assert "positive_prompt" in source
    assert "negative_prompt" in source
    assert "setNativeValue" in source
    assert "dispatchEvent(new Event(\"input\"" in source
    assert "dispatchEvent(new Event(\"change\"" in source


def test_gradio_extension_loads_studio_autofill_bridge() -> None:
    source = inspect.getsource(ui_gradio_extensions.javascript_html)

    assert "studio-autofill-bridge.js" in source
    assert "studio_autofill_bridge_js_path" in source
