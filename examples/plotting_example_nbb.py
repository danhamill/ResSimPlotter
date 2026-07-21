"""Example usage of the standardized plotting module (NBB, Standard op)."""
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
    'NBB': {
        'full_name': 'New Bullards Bar',
        'elevation_range': (1880, 1980),
        'zones': {
            'flood_control': 1956,
            'top_of_dam': 1965,
            'bottom_firo': 1894,
            'top_firo': 1929,
        },
    },
}


def create_nbb_system() -> System:
    nbb = Reservoir(
        name="NBB",
        full_name="New Bullards Bar",
        dss_location_code="NEW BULLARDS BAR",
    )
    return System(
        name="Feather-Yuba River System",
        reservoirs=[nbb],
        downstream_locations=[Dataset(name="FEATHER R + YUBA R", parameter="FLOW")],
    )


def main():
    shared_system = create_nbb_system()
    nbb_firo_target = Dataset(
        name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"
    )

    alternative_sim = Simulation(
        collectionID=100,
        alternativeID="RIC_F03A",
        trialID="0",
        dssFilePath=Path(
            r"C:\workspace\git_clones\Robustness_Viewer\data\Event_Model_Updated\1986_simulation_v7.dss"
        ),
        system=shared_system,
        operations={"NBB": create_standard_reservoir_operation()},
        zones={"NBB": [nbb_firo_target]},
    )

    baseline_sim1 = Simulation(
        collectionID=100,
        alternativeID="SS_FV03S-P75",
        trialID=None,
        dssFilePath=Path(
            r"C:\workspace\git_clones\Robustness_Viewer\data\FVA_config\SS-1986_results_v7.dss"
        ),
        system=shared_system,
        operations={"NBB": create_standard_reservoir_operation()},
    )

    alternative_sim.load_system_data()
    baseline_sim1.load_system_data()

    plotter = SimulationPlotter()
    nbb_cfg = RESERVOIR_CONFIG['NBB']

    detailed_config = PlotPresets.detailed_analysis()
    detailed_config.elevation_range = nbb_cfg['elevation_range']
    detailed_config.reservoir_full_name = nbb_cfg['full_name']
    detailed_config.zone_elevations = nbb_cfg['zones']
    detailed_config.height = 250
    detailed_config.width = 500

    print("Creating detailed plot with simulation-specific configuration...")
    detailed_plot = plotter.plot_reservoir(
        simulation=baseline_sim1,
        reservoir_name="NBB",
        config=detailed_config,
    )
    detailed_plot.show()
    detailed_plot.save(
        r"C:\workspace\YubaFeather\Models\EST\Documentation\Figures\nbb_example_fva.svg"
    )

    plotter.plot_comparison(
        alternative_simulation=alternative_sim,
        baseline_simulations=[baseline_sim1],
        baseline_shortname=['FVA'],
        reservoir_name="NBB",
        config=detailed_config,
    ).show()
    print("Comparison plot created successfully.")


if __name__ == "__main__":
    main()
