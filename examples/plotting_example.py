"""Example usage of the standardized plotting module (Oroville, Standard op)."""
from pathlib import Path

import altair as alt

from ressimplotter import (
    Dataset,
    PlotPresets,
    Reservoir,
    Simulation,
    SimulationPlotter,
    System,
    create_standard_reservoir_operation,
)

alt.renderers.enable('browser')


RESERVOIR_CONFIG = {
    'ORO': {
        'full_name': 'Oroville',
        'elevation_range': (840, 920),
        'zones': {
            'flood_control': 850,
            'top_conservation': 900,
            'surcharge': 910,
            'top_of_dam': 920,
        },
    },
}


def create_oroville_system() -> System:
    oro = Reservoir(name="ORO", full_name="Oroville", dss_location_code="OROVILLE")
    return System(
        name="Feather-Yuba River System",
        reservoirs=[oro],
        downstream_locations=[Dataset(name="FEATHER R + YUBA R", parameter="FLOW")],
    )


def main():
    shared_system = create_oroville_system()
    dss_path = Path(r"examples\exampleData.dss")
    oro_firo_target = Dataset(name="OROVILLE-FIRO TARGET", parameter="ELEV-ZONE")

    alternative_sim = Simulation(
        collectionID=100,
        alternativeID="RIC_F03A",
        trialID="0",
        dssFilePath=dss_path,
        system=shared_system,
        operations={"ORO": create_standard_reservoir_operation()},
        zones={"ORO": [oro_firo_target]},
    )

    baseline_sim1 = Simulation(
        collectionID=100,
        alternativeID="SS_FV03S-P75",
        trialID=None,
        dssFilePath=dss_path,
        system=shared_system,
        operations={"ORO": create_standard_reservoir_operation()},
    )

    alternative_sim.load_system_data()
    baseline_sim1.load_system_data()

    plotter = SimulationPlotter()
    oro_cfg = RESERVOIR_CONFIG['ORO']

    detailed_config = PlotPresets.detailed_analysis()
    detailed_config.elevation_range = oro_cfg['elevation_range']
    detailed_config.reservoir_full_name = oro_cfg['full_name']
    detailed_config.zone_elevations = oro_cfg['zones']
    detailed_config.height = 250
    detailed_config.width = 500

    print("Creating detailed plot with simulation-specific configuration...")
    plotter.plot_reservoir(
        simulation=alternative_sim,
        reservoir_name="ORO",
        config=detailed_config,
    ).show()

    plotter.plot_comparison(
        alternative_simulation=alternative_sim,
        baseline_simulations=[baseline_sim1],
        baseline_shortname=['FVA'],
        reservoir_name="ORO",
        config=detailed_config,
    ).show()
    print("Comparison plot created successfully.")


if __name__ == "__main__":
    main()
