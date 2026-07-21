import pytest
from pathlib import Path

from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.simulation import Simulation
from ressimplotter.dss_integration import TimeSeriesContainer


@pytest.fixture
def normal_operation():
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
def sample_reservoir_zones():
    return [
        Dataset(name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-BELOW FIRO SPACE", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-FLOOD CONTROL", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-FIRO SPACE", parameter="ELEV-ZONE"),
    ]


@pytest.fixture
def sample_reservoir():
    return Reservoir(
        name="NBB",
        full_name="New Bullards Bar Reservoir",
        dss_location_code="NEW BULLARDS BAR",
    )


@pytest.fixture
def sample_simulation(sample_reservoir, normal_operation, sample_reservoir_zones):
    return Simulation(
        collectionID=84,
        alternativeID="RID_F03A",
        dssFilePath=Path(r"test_data\test_data.dss"),
        trialID="0",
        reservoirs=[sample_reservoir],
        operations={sample_reservoir.name: normal_operation},
        zones={sample_reservoir.name: sample_reservoir_zones},
    )


def test_reservoir_creation(sample_reservoir):
    reservoir = sample_reservoir
    assert reservoir.name == "NBB"
    assert reservoir.full_name == "New Bullards Bar Reservoir"
    assert reservoir.dss_location_code == "NEW BULLARDS BAR"


def test_reservoir_has_no_operation_attribute(sample_reservoir):
    """Operations now live on Simulation, not Reservoir."""
    assert not hasattr(sample_reservoir, "operation")
    assert not hasattr(sample_reservoir, "zones")


def test_simulation_operation_access(sample_simulation):
    operation = sample_simulation.get_operation("NBB")
    assert operation is not None
    assert operation.operation_type == "Standard"
    assert operation.description == "Standard reservoir operation"


def test_simulation_datasets_initial_state(sample_simulation):
    """Datasets registered on the simulation start with no timeseries."""
    datasets = sample_simulation.operations["NBB"].datasets
    assert len(datasets) == 4
    for dataset in datasets:
        assert dataset.timeseries is None
        assert dataset.path is None


def test_simulation_dataset_names(sample_simulation):
    names = [d.name for d in sample_simulation.operations["NBB"].datasets]
    assert names == ["Elevation", "Outflow", "Inflow", "Storage"]


def test_simulation_dataset_parameters(sample_simulation):
    params = {d.name: d.parameter for d in sample_simulation.operations["NBB"].datasets}
    assert params == {
        "Elevation": "ELEV",
        "Outflow": "FLOW-OUT",
        "Inflow": "FLOW-IN",
        "Storage": "STOR",
    }


def test_simulation_load_all_datasets(sample_simulation):
    """load_system_data populates timeseries for both operation and zone datasets."""
    sample_simulation.load_system_data()

    loaded_op = sample_simulation.get_operation("NBB")
    loaded_ts = [d.timeseries for d in loaded_op.datasets if d.timeseries is not None]
    assert len(loaded_ts) == 4

    loaded_zones = sample_simulation.get_zones("NBB")
    loaded_zone_ts = [z.timeseries for z in loaded_zones if z.timeseries is not None]
    assert len(loaded_zone_ts) == 4


def test_individual_dataset_loading(sample_reservoir, sample_simulation):
    """Datasets can still be loaded individually via the DSS loader helper."""
    elevation_dataset = next(
        d for d in sample_simulation.operations["NBB"].datasets if d.name == "Elevation"
    )
    assert elevation_dataset.timeseries is None
    assert elevation_dataset.path is None

    elevation_dataset.load_reservoir_timeseries_from_dss(
        dss_file_path=Path(sample_simulation.dssFilePath),
        reservoir_dss_code=sample_reservoir.dss_location_code,
        time_step=sample_simulation.time_step,
        fpart=sample_simulation.build_fpart(),
    )

    expected_path = "//NEW BULLARDS BAR-POOL/ELEV//1HOUR/C:000084|RID_F03A--0/"
    assert elevation_dataset.path == expected_path


def test_reservoir_string_representation(sample_reservoir):
    expected = (
        "Reservoir(name=NBB, full_name=New Bullards Bar Reservoir, "
        "dss_location_code=NEW BULLARDS BAR)"
    )
    assert str(sample_reservoir) == expected
