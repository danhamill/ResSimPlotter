"""Tests for the global hecdss debug level, using the real test DSS file."""
from pathlib import Path

import pytest

import ressimplotter as rsp
from ressimplotter import dss_integration as di
from ressimplotter.dss_integration import DSSReader

TEST_DSS = Path("test_data/test_data.dss")


@pytest.fixture(autouse=True)
def _reset_debug_level():
    yield
    rsp.set_debug_level(None)


def test_exported():
    assert "set_debug_level" in rsp.__all__


@pytest.mark.parametrize("level", [None, 0, 1, 3])
def test_reads_work_with_global_debug_level(level):
    rsp.set_debug_level(level)
    reader = DSSReader(TEST_DSS)
    assert reader.get_catalog()
    path = next(p for p in reader.get_catalog() if "/ELEV/" in p)
    assert len(reader.read_time_series(path).values) > 0


def test_level_stored_globally():
    rsp.set_debug_level(2)
    assert di._DEBUG_LEVEL == 2


def test_open_dss_applies_level_to_real_file(monkeypatch):
    seen = []
    original = di.HecDss.set_debug_level
    monkeypatch.setattr(
        di.HecDss, "set_debug_level",
        lambda self, level: (seen.append(level), original(self, level))[1],
    )
    rsp.set_debug_level(3)
    DSSReader(TEST_DSS).get_catalog()
    assert seen == [3]


def test_missing_method_only_warns(monkeypatch, caplog):
    monkeypatch.delattr(di.HecDss, "set_debug_level")
    rsp.set_debug_level(3)
    assert DSSReader(TEST_DSS).get_catalog()
    assert "set_debug_level" in caplog.text
