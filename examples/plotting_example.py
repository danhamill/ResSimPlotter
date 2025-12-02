"""
Example usage of the standardized plotting module.

This demonstrates how to use the plotting module for both single simulation
plots and multi-simulation comparisons, including how to pass simulation-specific
configuration data.
"""

from pathlib import Path
from ressimplotter.plotting import SimulationPlotter
from ressimplotter.plotting.config import PlotPresets
from ressimplotter.simulation import Simulation
from ressimplotter.collections.system import System
from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.utils import create_standard_reservoir_operation
import altair as alt
alt.renderers.enable('browser')

# Simulation-specific data (would typically come from your project configuration)
RESERVOIR_CONFIG = {
    'NBB': {
        'full_name': 'New Bullards Bar',
        'elevation_range': (1800, 2000),  # Y-axis limits in feet
        'zones': {
            'flood_control': 1965,
            'top_conservation': 1955, 
            'surcharge': 1975,
            'top_of_dam': 1995
        }
    },
    'ORO': {
        'full_name': 'Oroville',
        'elevation_range': (840, 920),
        'zones': {
            'flood_control': 850,
            'top_conservation': 900,
            'surcharge': 910,
            'top_of_dam': 920
        }
    }
}

def create_example_system_nbb():
    """Create an example system for testing."""
    # Define downstream locations
    downstream_locations = [
        Dataset(name="FEATHER R + YUBA R", parameter="FLOW")
    ]

    # Define reservoirs
    nbb_reservoir = Reservoir(
        name="NBB",
        full_name="New Bullards Bar",
        dss_location_code="NEW BULLARDS BAR",
        operation=create_standard_reservoir_operation(), 
        zones=[
            Dataset(name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"),
            Dataset(name="NEW BULLARDS BAR-BELOW FIRO SPACE", parameter="ELEV-ZONE"),
            Dataset(name="NEW BULLARDS BAR-FLOOD CONTROL", parameter="ELEV-ZONE"),
            Dataset(name="NEW BULLARDS BAR-FIRO SPACE", parameter="ELEV-ZONE")
        ]
    )

    return System(
        name="Feather-Yuba River System",
        reservoirs=[nbb_reservoir],
        downstream_locations=downstream_locations
    )

def create_example_system_oroville():
    """Create an example system for testing."""
    # Define downstream locations
    downstream_locations = [
        Dataset(name="FEATHER R + YUBA R", parameter="FLOW")
    ]

    # Define reservoirs
    oro_reservoir = Reservoir(
        name="ORO",
        full_name="Oroville",
        dss_location_code="OROVILLE",
        operation=create_standard_reservoir_operation(), 
        zones=[
            Dataset(name="OROVILLE-FIRO TARGET", parameter="ELEV-ZONE"),
            # Dataset(name="OROVILLE-BELOW FIRO SPACE", parameter="ELEV-ZONE"),
            # Dataset(name="OROVILLE-FLOOD CONTROL", parameter="ELEV-ZONE"),
            # Dataset(name="OROVILLE-FIRO SPACE", parameter="ELEV-ZONE")
        ]
    )

    return System(
        name="Feather-Yuba River System",
        reservoirs=[oro_reservoir],
        downstream_locations=downstream_locations
    )

def main():
    """Demonstrate the plotting module usage."""
    
    # Create example simulations
    # Now we can reuse the same system object - each simulation will create independent copies
    shared_system = create_example_system_oroville()
    
    # Alternative simulation (the one being tested)
    alternative_sim = Simulation(
        collectionID=100,
        alternativeID="RIC_F03A",
        trialID="0", 
        dssFilePath=Path(r"examples\exampleData.dss"),
        system=shared_system
    )
    
    # Baseline simulations - can reuse the same system safely
    baseline_sim1 = Simulation(
        collectionID=100,
        alternativeID="SS_FV03S-P75",
        trialID=None,
        dssFilePath=Path(r"examples\exampleData.dss"),  
        system=shared_system
    )
    

    
    # Load data
    alternative_sim.load_system_data()
    baseline_sim1.load_system_data()

    # Create plotter instance
    plotter = SimulationPlotter()
    
    # Get NBB reservoir configuration
    oro_config_data = RESERVOIR_CONFIG['ORO']
    
    # Example 1: Plot with specific elevation range and zones
    print("Creating detailed plot with simulation-specific configuration...")
    detailed_config = PlotPresets.detailed_analysis()
    detailed_config.elevation_range = oro_config_data['elevation_range']
    detailed_config.reservoir_full_name = oro_config_data['full_name']
    detailed_config.zone_elevations = oro_config_data['zones']
    detailed_config.height = 250
    detailed_config.width = 500
    
    detailed_plot = plotter.plot_reservoir(
        simulation=alternative_sim,
        reservoir_name="ORO",
        config=detailed_config
    )
    detailed_plot.show()
    
    # Example 2: Multi-simulation comparison with configuration

    comparison_plot = plotter.plot_comparison(
        alternative_simulation=alternative_sim,
        baseline_simulations=[baseline_sim1],
        baseline_shortname=['FVA'],
        reservoir_name="ORO",
        config=detailed_config
    )
    comparison_plot.show()
    print("✓ Comparison plot created successfully!")
    

if __name__ == "__main__":
    main()
