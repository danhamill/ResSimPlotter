# ResSimPlotter

A Python package for reservoir simulation data management, processing, and visualization.

## Description

ResSimPlotter is a comprehensive Python package designed to help water resource engineers and reservoir simulation professionals manage, process, and visualize reservoir simulation data from DSS (Data Storage System) files and other formats.

## Features

- **DSS Integration**: Read and process time series data from HEC-DSS files
- **Modular Architecture**: Clean separation of components, collections, and simulation orchestration
- **Reservoir Modeling**: Model complex reservoir systems with operations, datasets, and time series
- **Data Management**: Organize datasets by reservoirs, operations, and downstream locations
- **Advanced Plotting**: Standardized visualization with Altair for single reservoirs and multi-simulation comparisons
- **Flexible Configuration**: Customizable plot settings, colors, and styling options
- **Lazy Loading**: Efficient data loading with independent system copies for comparison plotting
- **Comprehensive Testing**: Well-tested codebase with pytest integration
- **Type Safety**: Full type annotations for better development experience

## Architecture

The package follows a clean architectural pattern:

```
ressimplotter/
├── simulation.py           # Top-level orchestrator
├── components/             # Fundamental building blocks
│   ├── dataset.py         # Individual time series data
│   ├── reservoir.py       # Physical reservoir entities  
│   └── timeseries.py      # Core time series structures
├── collections/           # Container/grouping classes
│   ├── operation.py       # Collections of datasets
│   └── system.py          # Collections of reservoirs
├── plotting/              # Visualization and plotting
│   ├── __init__.py        # Main plotting interfaces
│   └── config.py          # Plot configuration and styling
└── dss_integration.py     # DSS file handling
```

## Quick Start

```python
from pathlib import Path

from ressimplotter import (
    Dataset, Reservoir, System, Simulation, SimulationPlotter,
    create_standard_reservoir_operation, create_firo_reservoir_operation,
)

# 1. Physical topology — reservoir dimensions and DSS location codes only.
nbb = Reservoir(
    name="NBB",
    full_name="New Bullards Bar",
    dss_location_code="NEW BULLARDS BAR",
)
system = System(
    name="Reservoir System",
    reservoirs=[nbb],
    downstream_locations=[],
)

# 2. Run-time policy — which Operation and zone datasets apply for THIS run.
#    Different simulations can bind different operations/zones to the same
#    physical reservoir (e.g. FIRO alternative vs Standard baseline).
alternative_sim = Simulation(
    collectionID=84,
    alternativeID="RID_F03A",
    dssFilePath=Path("path/to/your/data.dss"),
    system=system,
    operations={"NBB": create_firo_reservoir_operation()},
    zones={"NBB": [
        Dataset(name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"),
    ]},
)

baseline_sim = Simulation(
    collectionID=84,
    alternativeID="SS_FV03S-P75",
    dssFilePath=Path("path/to/your/data.dss"),
    system=system,
    operations={"NBB": create_standard_reservoir_operation()},
)

alternative_sim.load_system_data()
baseline_sim.load_system_data()

# 3. Plot.
plotter = SimulationPlotter()
plotter.plot_reservoir(alternative_sim, "NBB").show()
plotter.plot_comparison(
    alternative_simulation=alternative_sim,
    baseline_simulations=[baseline_sim],
    baseline_shortname=["FVA"],
    reservoir_name="NBB",
).show()
```

> The public API is re-exported from the top-level ``ressimplotter`` package,
> so a single ``from ressimplotter import ...`` covers the common case. Deep
> imports (``ressimplotter.simulation.Simulation`` etc.) still work.

### Data model in one paragraph

``Reservoir`` describes a physical dam (name, DSS location code, optional
ranges). ``Operation`` is a policy — the set of pool time series a given run
reads (elevation, in/out flow, storage). Zones are time-varying zone-elevation
datasets (e.g. a FIRO target curve). Both ``operations`` and ``zones`` live on
``Simulation`` (keyed by ``Reservoir.name``), so each run can bind a different
policy to the same physical reservoir. Static horizontal reference elevations
(top of dam, spillway crest) are drawn from ``PlotConfig.zone_elevations``.

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip
- HEC-DSS Python library (`hecdss`)

### Using Poetry (Recommended)

If you have Poetry installed:

```bash
git clone <repository-url>
cd ResSimPlotter
poetry install
```

### Using pip

```bash
# Base package only
pip install -e .

# With examples included (adds example scripts and data files)
pip install -e .[examples]
```

### Dependencies

The package requires:
- `hecdss` - For reading DSS files
- `altair` - For interactive plotting and visualization
- `vl-convert-python` - For plot rendering and export
- `pandas` - For data manipulation
- `numpy` - For numerical operations
- `pytest` - For testing (development)
- `dataclasses` and `typing` - For type safety (Python standard library)

## Development

This project uses Poetry for dependency management and follows modern Python development practices.

### Setup Development Environment

1. Install Poetry: https://python-poetry.org/docs/#installation
2. Clone this repository
3. Run `poetry install` to install dependencies
4. Run `poetry shell` to activate the virtual environment

### Project Structure

```
ResSimPlotter/
├── ressimplotter/          # Main package
│   ├── components/         # Core building blocks
│   ├── collections/        # Container classes
│   ├── simulation.py       # Simulation orchestrator
│   └── dss_integration.py  # DSS file handling
├── tests/                  # Test suite
├── examples/               # Usage examples
├── test_data/              # Sample DSS files for testing
└── pyproject.toml          # Project configuration
```

### Running Tests

```bash
poetry run pytest
```

Run specific test files:

```bash
poetry run pytest tests/test_reservoir.py -v
```

Run with coverage:

```bash
poetry run pytest --cov=ressimplotter
```

### Testing Philosophy

The project follows comprehensive testing practices:
- Unit tests for all components and collections
- Integration tests for DSS file loading
- Fixture-based testing for realistic scenarios
- Test data included in `test_data/` directory

### Code Quality

The project maintains high code quality standards:

```bash
# Type checking with ruff
poetry run ruff ressimplotter
```

## Examples

See the `examples/` directory for complete usage examples:

- `examples/plotting_example.py` - Complete plotting workflow with reservoir systems
- `examples/exampleData.dss` - Sample DSS data file for testing

To access examples after installation:

```python
import ressimplotter
# Examples are included when installed with: pip install ressimplotter[examples]
```

## API Reference

### Core Components

- **`Dataset`** - Individual time series data with DSS integration
- **`Reservoir`** - Physical reservoir description (name, DSS location code, ranges)
- **`TimeSeries`** - Core time series data structure

### Collections

- **`Operation`** - A named group of datasets (e.g. Standard, FIRO) that a run reads
- **`System`** - A named group of physical reservoirs and downstream locations

### Simulation

- **`Simulation`** - Binds run-time policy (``operations`` and ``zones``, keyed by
  reservoir name) to a topology and a DSS file. Handles loading.

### Plotting

- **`SimulationPlotter`** - Main interface for creating standardized plots
- **`ReservoirPlotter`** - Single reservoir visualization
- **`ComparisonPlotter`** - Multi-simulation comparison plots
- **`PlotConfig`** - Configuration for plot appearance and behavior

## DSS Integration

The package provides seamless integration with HEC-DSS files:

```python
# DSS paths are automatically constructed
# Format: //LOCATION/PARAMETER//TIMESTEP/F-PART/
# where F-PART = C:{collectionID:06d}|{alternativeID}[--{trialID}]
dss_path = "//NEW BULLARDS BAR-POOL/STOR//1HOUR/C:000084|RID_F03A--0/"

# Data is loaded on the simulation; each dataset in each registered operation
# (and each zone dataset) is fetched with one DSS read.
simulation.load_system_data()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`poetry run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Philosophy

- **Clean Architecture**: Maintain separation between components, collections, and orchestration
- **Type Safety**: Use type annotations throughout
- **Comprehensive Testing**: Write tests for all new functionality
- **Documentation**: Update README and docstrings for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- HEC-DSS team for the DSS file format and Python library
- Water resource engineering community for requirements and feedback