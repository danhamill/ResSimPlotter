"""Showcase: FIRO alternative vs Standard baselines on Oroville.

Demonstrates the new run-time-policy model:
  * Reservoir describes the physical dam.
  * Simulation binds an Operation and (optionally) zone datasets to that dam
    for a specific run.
  * Baseline runs and the alternative run can have different operations and
    different zones (e.g. only the FIRO alternative loads the FIRO target curve).
"""
from pathlib import Path

import altair as alt

from ressimplotter import (
    Dataset,
    PlotPresets,
    Reservoir,
    Simulation,
    SimulationPlotter,
    System,
    create_firo_reservoir_operation,
    create_standard_reservoir_operation,
)

alt.renderers.enable('browser')


RESERVOIR_CONFIG = {
    'NBB': {
        'full_name': 'New Bullards Bar',
        'elevation_range': (1880, 1980),
        'zones': {
            'flood_control': 1956,
            'top_of_dam': 1965,
        },
    },
    'ORO': {
        'full_name': 'Oroville',
        'elevation_range': (830, 920),
        'zones': {
            'surcharge': 910,
            'top_of_dam': 920,
        },
    },
}


def create_feather_yuba_system() -> System:
    """Physical description only. No operations, no zones."""
    oro = Reservoir(
        name="ORO",
        full_name="Oroville",
        dss_location_code="OROVILLE",
    )
    return System(
        name="Feather-Yuba River System",
        reservoirs=[oro],
        downstream_locations=[Dataset(name="FEATHER R + YUBA R", parameter="FLOW")],
    )


def main():
    dss_path = Path(r"test_data\test_data.dss")
    shared_system = create_feather_yuba_system()

    # FIRO target curve is a zone that only the FIRO alternative reads.
    oro_firo_target = Dataset(name="OROVILLE-FIRO TARGET", parameter="ELEV-ZONE")
    oro_top_fir= Dataset(name="OROVILLE-FIRO SPACE", parameter="ELEV-ZONE")
    oro_below_fir= Dataset(name="OROVILLE-BELOW FIRO SPACE", parameter="ELEV-ZONE")

    # Alternative run: FIRO operation + FIRO target zone.
    alternative_sim = Simulation(
        collectionID=100,
        alternativeID="RIG_F03E",
        trialID="0",
        dssFilePath=dss_path,
        system=shared_system,
        operations={"ORO": create_firo_reservoir_operation()},
        zones={"ORO": [oro_firo_target, oro_top_fir, oro_below_fir]},
    )

    # Baselines: standard operation, no zones.
    baseline_sim1 = Simulation(
        collectionID=100,
        alternativeID="RPG_F03E",
        trialID="0",
        dssFilePath=dss_path,
        system=shared_system,
        operations={"ORO": create_standard_reservoir_operation()},
    )
    baseline_sim2 = Simulation(
        collectionID=100,
        alternativeID="R_G_B00E",
        trialID="0",
        dssFilePath=dss_path,
        system=shared_system,
        operations={"ORO": create_standard_reservoir_operation()},
    )

    for sim in (alternative_sim, baseline_sim1, baseline_sim2):
        sim.load_system_data()

    plotter = SimulationPlotter()
    oro_cfg = RESERVOIR_CONFIG['ORO']

    detailed_config = PlotPresets.detailed_analysis()
    detailed_config.elevation_range = oro_cfg['elevation_range']
    detailed_config.reservoir_full_name = oro_cfg['full_name']
    detailed_config.zone_elevations = oro_cfg['zones']
    detailed_config.height = 250
    detailed_config.width = 500

    print("Single reservoir plot (FIRO alternative)...")
    plotter.plot_reservoir(
        simulation=alternative_sim,
        reservoir_name="ORO",
        config=detailed_config,
    ).show()

    print("Comparison plot (FIRO alt vs Standard baselines)...")
    plotter.plot_comparison(
        alternative_simulation=alternative_sim,
        baseline_simulations=[baseline_sim1, baseline_sim2],
        baseline_shortname=['Perfect', 'ID0'],
        reservoir_name="ORO",
        config=detailed_config,
    ).show()
    print("Comparison plot created successfully.")


if __name__ == "__main__":
    main()
