
# ResSimPlotter

Load HEC-ResSim results from DSS files and plot them with Altair: single-reservoir
operations plots, multi-simulation comparisons, and observed-data overlays.

## Installation

Requires Python 3.10+.

```bash
uv sync
```

## Quick start

```python
from pathlib import Path

import altair as alt
alt.renderers.enable('browser')

from ressimplotter import (
    Dataset,
    ObservedDataset,
    PlotPresets,
    Reservoir,
    Simulation,
    SimulationPlotter,
    System,
    create_standard_reservoir_operation,
)

# Physical topology: reservoir name and DSS location code.
pnf = Reservoir(
    name="PNF", full_name="Pine Flat Dam", dss_location_code="Pine Flat Dam"
)
system = System(name="Reservoir System", reservoirs=[pnf], downstream_locations=[])

# Run-time policy: operation, zones and observed records for THIS run.
sim = Simulation(
    collectionID=None,
    alternativeID="V1",
    dssFilePath=Path("simulation.dss"),
    system=system,
    operations={"PNF": create_standard_reservoir_operation()},
    zones={"PNF": [Dataset(name="Pine Flat Dam-Flood Control", parameter="STOR-ZONE")]},
    observed=[
        ObservedDataset(
            "Observed Storage",
            "/KINGS/PINE FLAT POOL/STOR-TOPCON//1Day/1953-2026/",
            panel="storage",
            dss_file=Path("observed.dss"),
        ),
        ObservedDataset(
            "Observed",
            "/KINGS/PINE FLAT/FLOW-RES OUT/01Oct1958 - 04Feb2026/1Day//",
            panel="outflow",
            dss_file=Path("observed.dss"),
        ),
    ],
    time_step="1Day",
)
sim.load_system_data()

config = PlotPresets.detailed_analysis()
config.storage_range = (200_000, 1_200_000)  # acre-ft
config.zone_storages = {"top_of_dam": 1_129_823}  # acre-ft
config.title_suffix = "2017"

SimulationPlotter().plot_operations(sim, "PNF", config=config).show()
```

The public API is re-exported from `ressimplotter`; deep imports also work.

## Concepts

- **`Reservoir` / `System`**: physical topology (names and DSS location codes).
- **`Operation`**: the pool time series a run reads. `create_standard_reservoir_operation()`
  reads `ELEV`, `FLOW-IN`, `FLOW-OUT` and `STOR`; `create_firo_reservoir_operation()`
  is the same set for FIRO runs.
- **Zones**: `Dataset` records drawn as reference curves, registered on `Simulation.zones`.
  `STOR-ZONE` records go on the storage panel; other parameters go on the elevation panel.
- **`Simulation`**: binds operations, zones, observed records, a topology and a DSS file,
  and loads the data (`load_system_data()` returns a `LoadReport`; check `.ok`).

Operations, zones and observed records are keyed by or attached to the `Simulation`, so
different runs can use different policies on the same reservoir.

## DSS paths

Paths are built as `//{location}-POOL/{parameter}//{time_step}/{F-part}/`.
`Simulation.time_step` (default `"1HOUR"`) is the E-part. The F-part depends on the model:

| Model              | Arguments                                     | F-part                   |
| ------------------ | --------------------------------------------- | ------------------------ |
| With collection    | `collectionID=84, alternativeID="RID_F03A"` | `C:000084\|RID_F03A--0` |
| Without collection | `collectionID=None, alternativeID="V1"`     | `V1--------0`          |

Without a collection the F-part is `{alternativeID}`, `-` padding and `{trialID}`
(default `"0"`), at a fixed width of 11 characters. `ValueError` is raised if the IDs
are too long.

## Plots

`SimulationPlotter` methods:

- `plot_reservoir(sim, name, config)`: elevation over flow.
- `plot_operations(sim, name, config)`: storage over flow. Needs `STOR-ZONE` zone datasets
  and `PlotConfig.storage_range` / `zone_storages` (acre-ft).
- `plot_comparison(alternative_simulation, baseline_simulations, baseline_shortname, reservoir_name)`:
  compare one alternative with baselines. Elevation and flow only.

`PlotConfig` controls size, ranges, colours, legend and titles. Useful fields:
`elevation_range`, `zone_elevations`, `storage_range`, `zone_storages`,
`reservoir_full_name`, `title_suffix`, `title_include_simulation`.
`PlotPresets` provides ready-made configurations such as `detailed_analysis()`.

The title is `{reservoir} (simulation: {alternativeID}-{title_suffix})`, or
`{reservoir} - {title_suffix}` when `title_include_simulation` is `False`.

## Observed data

`ObservedDataset(name, dss_path, panel, dss_file=None)` overlays a record given by its
full DSS path. `dss_file=None` reads from the simulation's DSS file. `panel` is one of:

| Panel         | Plot      | Style         |
| ------------- | --------- | ------------- |
| `elevation` | elevation | black, solid  |
| `storage`   | storage   | black, solid  |
| `outflow`   | flow      | black, solid  |
| `inflow`    | flow      | black, dashed |

Records are clipped to the modeled time window, so any simulation period works. Units
are not converted and must match the model. Each dataset's `name` is its legend label.
Load failures are reported in the `LoadReport`.

## Development

```bash
uv run pytest
```

Tests use `test_data/test_data.dss`. Code lives in `ressimplotter/`: `simulation.py`,
`components/` (dataset, reservoir, time series), `collections/` (operation, system),
`plotting/` (plotters and `config.py`) and `dss_integration.py`. Run one DSS test
process at a time to avoid corrupting the test file.

## License

MIT. See `LICENSE`.
