import pytest
from pathlib import Path

from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.collections.system import System
from ressimplotter.simulation import Simulation
from ressimplotter.dss_integration import TimeSeriesContainer


@pytest.fixture
def sample_reservoir_zones():
    return [
        Dataset(name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-BELOW FIRO SPACE", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-FLOOD CONTROL", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-FIRO SPACE", parameter="ELEV-ZONE"),
    ]


def _make_standard_operation() -> Operation:
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


@pytest.fixture
def sample_reservoir_list():
    return [
        Reservoir(
            name="NBB",
            full_name="New Bullards Bar Reservoir",
            dss_location_code="NEW BULLARDS BAR",
        ),
        Reservoir(
            name="ORO",
            full_name="Oroville Reservoir",
            dss_location_code="OROVILLE",
        ),
    ]


@pytest.fixture
def sample_dataset():
    return Dataset(name="FEATHER R + YUBA R", parameter="FLOW")


@pytest.fixture
def sample_system(sample_reservoir_list, sample_dataset):
    return System(
        name="Feather-Yuba System",
        reservoirs=sample_reservoir_list,
        downstream_locations=[sample_dataset],
    )


@pytest.fixture
def sample_simulation(sample_system, sample_reservoir_zones):
    return Simulation(
        collectionID=84,
        alternativeID="RID_F03A",
        dssFilePath=Path(r"test_data\test_data.dss"),
        system=sample_system,
        trialID="0",
        operations={
            "NBB": _make_standard_operation(),
            "ORO": _make_standard_operation(),
        },
        zones={"NBB": sample_reservoir_zones},
    )


def test_system_creation(sample_system):
    assert sample_system.name == "Feather-Yuba System"
    assert len(sample_system.reservoirs) == 2
    assert len(sample_system.downstream_locations) == 1


def test_system_string_representation(sample_system):
    expected = (
        "System(name=Feather-Yuba System, reservoirs=['NBB', 'ORO'], "
        "downstream_locations=['FEATHER R + YUBA R'])"
    )
    assert str(sample_system) == expected


def test_system_load_data(sample_simulation):
    sim = sample_simulation
    sim.load_system_data()

    # Downstream locations loaded in place
    for location in sim._own_downstream_locations():
        assert location.timeseries is not None
        assert isinstance(location.timeseries, TimeSeriesContainer)

    # Reservoir operation datasets loaded
    for reservoir_name in ["NBB", "ORO"]:
        operation = sim.get_operation(reservoir_name)
        for dataset in operation.datasets:
            assert dataset.timeseries is not None
            assert isinstance(dataset.timeseries, TimeSeriesContainer)

    # Zone datasets loaded (only NBB has zones registered)
    for zone_dataset in sim.get_zones("NBB"):
        assert zone_dataset.timeseries is not None
        assert isinstance(zone_dataset.timeseries, TimeSeriesContainer)

    # ORO has no zones registered
    assert sim.get_zones("ORO") == []
