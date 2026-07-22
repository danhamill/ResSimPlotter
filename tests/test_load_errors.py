"""Tests for strict-load behavior and structured DSS load errors."""
from pathlib import Path

import pytest

from ressimplotter import (
    Dataset,
    DSSFileNotFound,
    DSSLoadError,
    DSSPathNotFound,
    LoadReport,
    Operation,
    Reservoir,
    Simulation,
    System,
)


TEST_DSS = Path("test_data/test_data.dss")
GOOD_ALT = "RID_F03A"
GOOD_COLLECTION = 84


def _standard_op() -> Operation:
    return Operation(
        operation_type="Standard",
        description="Standard reservoir operation",
        datasets=[
            Dataset(name="Elevation", parameter="ELEV"),
            Dataset(name="Outflow", parameter="FLOW-OUT"),
            Dataset(name="Inflow", parameter="FLOW-IN"),
            Dataset(name="Storage", parameter="STOR"),
        ],
    )


def _make_sim(alternative_id: str = GOOD_ALT,
              collection_id: int = GOOD_COLLECTION,
              dss_path: Path = TEST_DSS) -> Simulation:
    nbb = Reservoir(name="NBB", full_name="New Bullards Bar",
                    dss_location_code="NEW BULLARDS BAR")
    system = System(
        name="test",
        reservoirs=[nbb],
        downstream_locations=[Dataset(name="FEATHER R + YUBA R", parameter="FLOW")],
    )
    return Simulation(
        collectionID=collection_id,
        alternativeID=alternative_id,
        trialID="0",
        dssFilePath=dss_path,
        system=system,
        operations={"NBB": _standard_op()},
    )


def test_missing_dss_file_raises_in_strict_mode():
    sim = _make_sim(dss_path=Path("does_not_exist.dss"))
    with pytest.raises(DSSLoadError) as exc:
        sim.load_system_data()
    assert "does_not_exist.dss" in str(exc.value)


def test_missing_dss_file_returns_report_in_nonstrict_mode():
    sim = _make_sim(dss_path=Path("does_not_exist.dss"))
    report = sim.load_system_data(strict=False)
    assert isinstance(report, LoadReport)
    assert not report.ok
    assert report.read_errors  # <file> failure recorded


def test_bad_alternative_id_flagged_by_fpart_preflight():
    sim = _make_sim(alternative_id="RIG_TYPO")
    with pytest.raises(DSSLoadError) as exc:
        sim.load_system_data()
    msg = str(exc.value)
    assert "F-part" in msg
    assert "RIG_TYPO" in msg
    assert "typo" in msg.lower()


def test_bad_alternative_id_report_in_nonstrict_mode():
    sim = _make_sim(alternative_id="RIG_TYPO")
    report = sim.load_system_data(strict=False)
    assert report.fpart_missing is not None
    assert "RIG_TYPO" in report.fpart_missing
    # Preflight short-circuits; per-dataset loads should not have run.
    assert not report.missing_paths
    assert not report.successes


def test_missing_reservoir_in_operations_reported():
    """Operation registered for a reservoir not in the system."""
    nbb = Reservoir(name="NBB", full_name="New Bullards Bar",
                    dss_location_code="NEW BULLARDS BAR")
    system = System(name="test", reservoirs=[nbb], downstream_locations=[])
    sim = Simulation(
        collectionID=GOOD_COLLECTION,
        alternativeID=GOOD_ALT,
        trialID="0",
        dssFilePath=TEST_DSS,
        system=system,
        operations={"ORO": _standard_op()},   # ORO not in system
    )
    with pytest.raises(DSSLoadError) as exc:
        sim.load_system_data()
    assert "ORO" in str(exc.value)


def test_successful_load_returns_ok_report():
    sim = _make_sim()
    report = sim.load_system_data()   # strict=True; must not raise
    assert isinstance(report, LoadReport)
    assert report.ok
    assert report.successes


def test_dataset_direct_load_raises_dssfilenotfound():
    ds = Dataset(name="OROVILLE-POOL", parameter="ELEV")
    with pytest.raises(DSSFileNotFound):
        ds.load_reservoir_timeseries_from_dss(
            dss_file_path=Path("nope.dss"),
            reservoir_dss_code="OROVILLE",
            time_step="1HOUR",
            fpart="C:000001|FAKE--0",
        )


def test_dataset_direct_load_raises_dsspathnotfound():
    ds = Dataset(name="OROVILLE-POOL", parameter="ELEV")
    with pytest.raises(DSSPathNotFound):
        ds.load_reservoir_timeseries_from_dss(
            dss_file_path=TEST_DSS,
            reservoir_dss_code="OROVILLE",
            time_step="1HOUR",
            fpart="C:999999|NOT_REAL--0",
        )
