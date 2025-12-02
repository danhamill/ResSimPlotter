import pytest
from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from pathlib import Path
from ressimplotter.simulation import Simulation
from ressimplotter.dss_integration import TimeSeriesContainer

@pytest.fixture
def normal_operation():
    ops = Operation(
        operation_type="Standard",
        description="Standard reservoir operation",
        datasets=[
        Dataset(
            name="Elevation",
            parameter="ELEV", 
            # units="FEET",
        ),
        Dataset(
            name="Outflow",
            parameter="FLOW-OUT",
            # units="CFS", 
        ),
        Dataset(
            name="Inflow", 
            parameter="FLOW-IN",
            # units="CFS",
        ),
         Dataset(
            name="Storage",
            parameter="STOR",
            # units="AF",
        ),
        
    ]

    )
    return ops

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
def sample_reservoir(normal_operation, sample_reservoir_zones):
    return Reservoir(
        name="NBB",
        full_name="New Bullards Bar Reservoir",
        dss_location_code="NEW BULLARDS BAR",
        operation=normal_operation,
        zones = sample_reservoir_zones
    )

@pytest.fixture
def sample_simulation(sample_reservoir):
    return Simulation(
        collectionID=84,
        alternativeID="RID_F03A",
        dssFilePath=Path(r"test_data\test_data.dss"),
        downstream_locations=[],  # Empty for reservoir tests
        trialID="0",
        reservoirs=[sample_reservoir]
    )

def test_reservoir_creation(sample_reservoir):
    """Test that Reservoir objects are created with correct properties."""
    reservoir = sample_reservoir
    assert reservoir.name == "NBB"
    assert reservoir.full_name == "New Bullards Bar Reservoir"
    assert reservoir.dss_location_code == "NEW BULLARDS BAR"
    assert reservoir.operation.operation_type == "Standard"

def test_reservoir_operation_access(sample_reservoir):
    """Test accessing the reservoir's operation."""
    reservoir = sample_reservoir
    operation = reservoir.operation
    assert operation is not None
    assert operation.operation_type == "Standard"
    assert operation.description == "Standard reservoir operation"

def test_reservoir_datasets_initial_state(sample_reservoir):
    """Test that reservoir datasets initially have no timeseries data."""
    reservoir = sample_reservoir
    datasets = reservoir.operation.datasets
    
    # Should have 4 datasets
    assert len(datasets) == 4
    
    # All datasets should initially have no timeseries or path
    for dataset in datasets:
        assert dataset.timeseries is None
        assert dataset.path is None

def test_reservoir_dataset_names(sample_reservoir):
    """Test that reservoir has the expected datasets."""
    reservoir = sample_reservoir
    datasets = reservoir.operation.datasets
    
    dataset_names = [dataset.name for dataset in datasets]
    expected_names = ["Elevation", "Outflow", "Inflow", "Storage"]
    assert dataset_names == expected_names

def test_reservoir_dataset_parameters(sample_reservoir):
    """Test that reservoir datasets have correct parameters."""
    reservoir = sample_reservoir
    datasets = reservoir.operation.datasets
    
    dataset_params = {dataset.name: dataset.parameter for dataset in datasets}
    expected_params = {
        "Elevation": "ELEV",
        "Outflow": "FLOW-OUT", 
        "Inflow": "FLOW-IN",
        "Storage": "STOR"
    }
    assert dataset_params == expected_params

def test_reservoir_load_all_datasets(sample_reservoir, sample_simulation):
    """Test that load_timeseries_from_dss loads data for all datasets."""
    reservoir = sample_reservoir
    simulation = sample_simulation
    
    # Initially no datasets should have timeseries
    for dataset in reservoir.operation.datasets:
        assert dataset.timeseries is None
        assert dataset.path is None
    
    # Load data for all datasets
    reservoir.load_timeseries_from_dss(simulation)

    assert len([i.timeseries for i in reservoir.operation.datasets if i.timeseries is not None]) == 4

    # Load zone datasets

    if reservoir.zones:
        reservoir.load_zone_datasets_from_dss(
            simulation
        )

        assert len([zone.timeseries for zone in reservoir.zones if zone.timeseries is not None]) == 4 

def test_individual_dataset_loading(sample_reservoir, sample_simulation):
    """Test loading individual dataset timeseries."""
    reservoir = sample_reservoir  
    simulation = sample_simulation
    
    # Get the elevation dataset
    elevation_dataset = next(d for d in reservoir.operation.datasets if d.name == "Elevation")
    
    # Initially should have no data
    assert elevation_dataset.timeseries is None
    assert elevation_dataset.path is None
    
    # Load data for just this dataset using the new method signature

    elevation_dataset.load_reservoir_timeseries_from_dss(
        dss_file_path=Path(simulation.dssFilePath),
        reservoir_dss_code=reservoir.dss_location_code,
        time_step=simulation.time_step,
        fpart=simulation.build_fpart()
    )
    
    # Should now have path set
    expected_path = "//NEW BULLARDS BAR-POOL/ELEV//1HOUR/C:000084|RID_F03A--0/"
    assert elevation_dataset.path == expected_path

def test_reservoir_string_representation(sample_reservoir):
    """Test Reservoir string representation."""
    reservoir = sample_reservoir
    expected_string = "Reservoir(name=NBB, full_name=New Bullards Bar Reservoir, dss_location_code=NEW BULLARDS BAR, operations=Operation(type=Standard, description=Standard reservoir operation, datasets=[Elevation, Outflow, Inflow, Storage]))"
    assert str(reservoir) == expected_string
    