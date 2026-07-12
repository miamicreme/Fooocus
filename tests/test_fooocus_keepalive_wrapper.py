from __future__ import annotations

import inspect

from scripts import run_fooocus_keepalive


def test_keepalive_wrapper_catches_clean_system_exit() -> None:
    source = inspect.getsource(run_fooocus_keepalive.run_launch)

    assert "except SystemExit" in source
    assert "exc.code in (None, 0)" in source


def test_keepalive_wrapper_has_explicit_loop() -> None:
    source = inspect.getsource(run_fooocus_keepalive.keepalive_loop)

    assert "while True" in source
    assert "time.sleep(3600)" in source
