import pytest
from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.collections.system import System
from pathlib import Path
from ressimplotter.simulation import Simulation
from ressimplotter.dss_integration import TimeSeriesContainer

@pytest.fixture
def sample_reservoir_zones():
    return [
        Dataset(
            name="NEW BULLARDS BAR-FIRO TARGET",
            parameter = "ELEV-ZONE"
        ),
        Dataset(
            name = "NEW BULLARDS BAR-BELOW FIRO SPACE",
            parameter = "ELEV-ZONE"
        ),
        Dataset(
            name = "NEW BULLARDS BAR-FLOOD CONTROL",
            parameter = "ELEV-ZONE"
        ),
        Dataset(
            name = "NEW BULLARDS BAR-FIRO SPACE",
            parameter = "ELEV-ZONE"
        )
    ]

@pytest.fixture
def sample_operation():
    ops = Operation(
        operation_type="Standard",
        description="Standard reservoir operation",
        datasets=[
            Dataset(
                name="Elevation",
                parameter="ELEV", 
            ),
            Dataset(
                name="Outflow",
                parameter="FLOW-OUT",
            ),
            Dataset(
                name="Inflow", 
                parameter="FLOW-IN",
            ),
            Dataset(
                name="Storage",
                parameter="STOR",
            ),
        ]
    )
    return ops

@pytest.fixture
def sample_reservoir_list(sample_operation, sample_reservoir_zones):
    return [
        Reservoir(
        name="NBB",
        full_name="New Bullards Bar Reservoir",
        dss_location_code="NEW BULLARDS BAR",
        operation=sample_operation,
        zones = sample_reservoir_zones
        ),
        Reservoir(
            name="ORO",
            full_name="Oroville Reservoir",
            dss_location_code="OROVILLE",
            operation=sample_operation
        )]

@pytest.fixture
def sample_dataset():
    return Dataset(
        name="FEATHER R + YUBA R",
        parameter="FLOW"
    )

@pytest.fixture
def sample_system(sample_reservoir_list, sample_dataset):
    return System(
        name="Feather-Yuba System",
        reservoirs=sample_reservoir_list,
        downstream_locations=[sample_dataset],
    )  

@pytest.fixture
def sample_simulation(sample_system):
    return Simulation(
        collectionID=84,
        alternativeID="RID_F03A",
        dssFilePath=Path(r"test_data\test_data.dss"),
        system=sample_system,
        trialID="0",
    )

def test_system_creation(sample_system):
    """Test that System objects are created with correct properties."""
    system = sample_system
    assert system.name == "Feather-Yuba System"
    assert len(system.reservoirs) == 2
    assert len(system.downstream_locations) == 1

def test_system_string_representation(sample_system):
    """Test System string representation."""
    system = sample_system
    expected_string = "System(name=Feather-Yuba System, reservoirs=['NBB', 'ORO'], downstream_locations=['FEATHER R + YUBA R'])"
    assert str(system) == expected_string

def test_system_load_data(sample_simulation):
    sim = sample_simulation

    sim.load_system_data()

    # Check that downstream location data is loaded via the independent system
    independent_system = getattr(sim, '_independent_system', None)
    assert independent_system is not None, "Independent system should be created after loading"
    
    for location in independent_system.downstream_locations:
        assert location.timeseries is not None
        assert isinstance(location.timeseries, TimeSeriesContainer)

    # Check reservoir data via simulation's get_reservoir_by_name method
    for reservoir_name in [res.name for res in sim.system.reservoirs]:
        loaded_reservoir = sim.get_reservoir_by_name(reservoir_name)
        assert loaded_reservoir is not None
        
        for dataset in loaded_reservoir.operation.datasets:
            assert dataset.timeseries is not None
            assert isinstance(dataset.timeseries, TimeSeriesContainer)

        if loaded_reservoir.zones:
            for zone_dataset in loaded_reservoir.zones:
                assert zone_dataset.timeseries is not None
                assert isinstance(zone_dataset.timeseries, TimeSeriesContainer)