from pathlib import Path

import pytest

from ressimplotter import (
    Dataset,
    ObservedDataset,
    PlotConfig,
    Reservoir,
    Simulation,
    SimulationPlotter,
    System,
    create_standard_reservoir_operation,
)
from ressimplotter.plotting import ReservoirPlotter

DSS = Path(__file__).resolve().parent.parent / "test_data" / "test_data.dss"
OBS_STOR = "/KINGS/PINE FLAT POOL/STOR-TOPCON//1Day/1953-2026/"
OBS_OUT = "/KINGS/PINE FLAT/FLOW-RES OUT//1Day//"


@pytest.fixture
def pine_flat_sim():
    pnf = Reservoir(
        name="PNF", full_name="Pine Flat Dam", dss_location_code="Pine Flat Dam"
    )
    sim = Simulation(
        collectionID=None,
        alternativeID="V1",
        dssFilePath=DSS,
        system=System(name="System", reservoirs=[pnf], downstream_locations=[]),
        operations={"PNF": create_standard_reservoir_operation()},
        zones={
            "PNF": [
                Dataset(name="Pine Flat Dam-Rain Flood", parameter="STOR-ZONE"),
                Dataset(name="Pine Flat Dam-Conservation", parameter="STOR-ZONE"),
                Dataset(name="Pine Flat Dam-Flood Control", parameter="STOR-ZONE"),
            ]
        },
        observed=[
            ObservedDataset("Observed Storage", OBS_STOR, panel="storage"),
            ObservedDataset("Observed", OBS_OUT, panel="outflow"),
        ],
        time_step="1Day",
    )
    report = sim.load_system_data()
    assert report.ok, report.format()
    return sim


def test_observed_rejects_unknown_panel():
    with pytest.raises(ValueError):
        ObservedDataset("x", "//A/B//1Day/C/", panel="bogus")


def test_observed_data_clipped_to_model_window(pine_flat_sim):
    data = ReservoirPlotter(PlotConfig()).extract_reservoir_data(
        pine_flat_sim, "PNF", include_storage=True
    )
    model = data["elevation"].datetime
    for key in ("observed_storage", "observed_outflow"):
        assert not data[key].empty
        assert data[key].datetime.min() >= model.min()
        assert data[key].datetime.max() <= model.max()


def test_plot_operations_includes_observed_in_legend(pine_flat_sim):
    config = PlotConfig(
        storage_range=(0, 1_200_000),
        zone_storages={"top_of_dam": 1_129_823},
        title_suffix="2017",
    )
    chart = SimulationPlotter().plot_operations(pine_flat_sim, "PNF", config=config)
    spec = chart.to_json()
    assert "Observed Storage" in spec
    assert '"Observed"' in spec
