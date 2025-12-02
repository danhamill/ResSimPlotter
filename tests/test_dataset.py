import pytest
import pandas as pd
from ressimplotter.components.dataset import Dataset
from pathlib import Path
from ressimplotter.simulation import Simulation
from ressimplotter.dss_integration import TimeSeriesContainer

@pytest.fixture
def sample_dataset():
    return Dataset(
        name="FEATHER R + YUBA R",
        parameter="FLOW"
    )

@pytest.fixture
def sample_simulation(sample_dataset):
    return Simulation(
        collectionID=84,
        alternativeID="RID_F03A",
        dssFilePath=Path(r"test_data\test_data.dss"),
        downstream_locations=[sample_dataset],
        trialID="0",
        reservoirs=None
    )

def test_dataset_string(sample_dataset):
    location = sample_dataset
    expected_str = "Dataset(FLOW at FEATHER R + YUBA R: not loaded, path=None)"
    assert str(location) == expected_str

# Test Location creation and basic properties
def test_dataset_creation(sample_dataset):
    """Test that Location objects are created with correct properties."""
    location = sample_dataset
    assert location.name == "FEATHER R + YUBA R"
    assert location.parameter == "FLOW"
    assert location.timeseries is None

def test_dataset_string_representation(sample_dataset):
    """Test Dataset string representation."""
    location = sample_dataset
    expected_str = "Dataset(FLOW at FEATHER R + YUBA R: not loaded, path=None)"
    assert str(location) == expected_str

# Test Simulation creation and basic properties
def test_simulation_creation(sample_simulation):
    """Test that Simulation objects are created with correct properties."""
    sim = sample_simulation
    assert sim.collectionID == 84
    assert sim.alternativeID == "RID_F03A"
    assert sim.trialID == "0"
    assert len(sim.downstream_locations) == 1

def test_simulation_string_representation(sample_simulation):
    """Test Simulation string representation."""
    sim = sample_simulation
    expected_string = "Simulation(collectionID=84, alternativeID=RID_F03A, trialID=0)"
    assert str(sim) == expected_string

def test_simulation_get_downstream_location_names(sample_simulation):
    """Test retrieving downstream location names from simulation."""
    sim = sample_simulation
    location_names = sim.get_all_downstream_location_names()
    assert location_names == ["FEATHER R + YUBA R"]

# Test TimeSeries loading functionality
def test_dataset_initial_timeseries_state(sample_simulation):
    """Test that locations initially have no timeseries data."""
    sim = sample_simulation
    location = sim.downstream_locations[0]
    assert location.timeseries is None

def test_simulation_load_data_creates_timeseries(sample_simulation):
    """Test that load_simulation_data creates timeseries for locations."""
    sim = sample_simulation
    location = sim.downstream_locations[0]
    
    # Before loading - no timeseries
    assert location.timeseries is None
    
    # Load data
    sim.load_downstream_location_data()
    
    # After loading - timeseries should exist
    assert location.timeseries is not None

def test_loaded_timeseries_properties(sample_simulation):
    """Test properties of timeseries after loading from DSS."""
    sim = sample_simulation
    sim.load_downstream_location_data()
    
    location = sim.downstream_locations[0]
    timeseries = location.timeseries
    
    assert isinstance(timeseries, TimeSeriesContainer)
    assert timeseries.path == '//FEATHER R + YUBA R/FLOW//1HOUR/C:000084|RID_F03A--0/'
    assert timeseries.interval == 3600

def test_dataset_string_after_loading_timeseries(sample_simulation):
    """Test Location string representation after loading timeseries."""
    sim = sample_simulation
    sim.load_downstream_location_data()
    
    location = sim.downstream_locations[0]
    expected_str_start = "Dataset(FLOW at FEATHER R + YUBA R: 529 records from 1996-12-18 04:00:00, cfs, path=//FEATHER R + YUBA R/FLOW//1HOUR/C:000084|RID_F03A--0/)"
    actual_str = str(location)
    assert actual_str.startswith(expected_str_start)


# Test DataFrame conversion functionality
def test_dataset_to_dataframe_without_timeseries(sample_dataset):
    """Test that to_dataframe raises error when no timeseries is loaded."""
    dataset = sample_dataset
    
    with pytest.raises(ValueError) as exc_info:
        dataset.to_dataframe()
    
    assert "No timeseries data loaded" in str(exc_info.value)
    assert dataset.name in str(exc_info.value)

def test_dataset_to_dataframe_with_timeseries(sample_simulation):
    """Test converting loaded timeseries data to pandas DataFrame."""
    sim = sample_simulation
    sim.load_downstream_location_data()
    
    location = sim.downstream_locations[0]
    df = location.to_dataframe()
    
    # Check DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == 'datetime'  # datetime should be index
    assert 'FLOW' in df.columns  # parameter should be column name
    assert len(df) > 0  # should have data
    
    # Check metadata attributes
    assert df.attrs['name'] == "FEATHER R + YUBA R"
    assert df.attrs['parameter'] == "FLOW"
    assert df.attrs['path'] == '//FEATHER R + YUBA R/FLOW//1HOUR/C:000084|RID_F03A--0/'

def test_dataset_to_dataframe_with_metadata(sample_simulation):
    """Test converting timeseries to DataFrame with metadata columns."""
    sim = sample_simulation
    sim.load_downstream_location_data()
    
    location = sim.downstream_locations[0]
    df = location.to_dataframe_with_metadata()
    
    # Check DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert 'datetime' in df.columns
    assert 'value' in df.columns
    assert 'name' in df.columns
    assert 'parameter' in df.columns
    assert 'units' in df.columns
    
    # Check data content
    assert df['name'].iloc[0] == "FEATHER R + YUBA R"
    assert df['parameter'].iloc[0] == "FLOW"