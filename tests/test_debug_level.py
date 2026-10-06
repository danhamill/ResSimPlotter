import logging

import pytest

from ressimplotter import dss_integration as di


class _Fake:
    calls = []

    def __init__(self, path):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def set_debug_level(self, level):
        _Fake.calls.append(level)



@pytest.fixture(autouse=True)
def _reset():
    _Fake.calls = []
    yield
    di.set_debug_level(None)


def test_default_not_called(monkeypatch):
    monkeypatch.setattr(di, "HecDss", _Fake, raising=False)
    with di._open_dss("x.dss"):
        pass
    assert _Fake.calls == []


def test_global_level_applied(monkeypatch):
    monkeypatch.setattr(di, "HecDss", _Fake, raising=False)
    di.set_debug_level(3)
    with di._open_dss("x.dss"):
        pass
    assert _Fake.calls == [3]


def test_missing_method_warns(monkeypatch, caplog):
    class Old:
        def __init__(self, path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(di, "HecDss", Old, raising=False)
    di.set_debug_level(2)
    with caplog.at_level(logging.WARNING):
        with di._open_dss("x.dss"):
            pass
    assert "set_debug_level" in caplog.text
