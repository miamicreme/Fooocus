from __future__ import annotations

import inspect

from scripts import run_fooocus_keepalive


class FakeReadTimeout(Exception):
    pass


def test_keepalive_wrapper_catches_clean_system_exit() -> None:
    source = inspect.getsource(run_fooocus_keepalive.run_launch)

    assert "except SystemExit" in source
    assert "exc.code in (None, 0)" in source


def test_keepalive_wrapper_recognizes_gradio_probe_timeout() -> None:
    exc = FakeReadTimeout("HTTPConnectionPool(host='127.0.0.1', port=7865): Read timed out. (read timeout=3)")

    assert run_fooocus_keepalive.is_gradio_startup_probe_timeout(exc)


def test_keepalive_wrapper_has_explicit_loop() -> None:
    source = inspect.getsource(run_fooocus_keepalive.keepalive_loop)

    assert "while True" in source
    assert "time.sleep(3600)" in source
