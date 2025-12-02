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
from ressimplotter.simulation import Simulation
from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.collections.system import System
from ressimplotter.plotting import SimulationPlotter, PlotConfig
from ressimplotter.utils import create_standard_reservoir_operation
from pathlib import Path

# Create a reservoir with standard operations
reservoir = Reservoir(
    name="NBB",
    full_name="New Bullards Bar",
    dss_location_code="NEW BULLARDS BAR",
    operation=create_standard_reservoir_operation(),
    zones=[
        Dataset(name="NEW BULLARDS BAR-FIRO TARGET", parameter="ELEV-ZONE"),
        Dataset(name="NEW BULLARDS BAR-FLOOD CONTROL", parameter="ELEV-ZONE")
    ]
)

# Create a system containing the reservoir
system = System(
    name="Reservoir System",
    reservoirs=[reservoir],
    downstream_locations=[]
)

# Create and load simulation data
simulation = Simulation(
    collectionID=84,
    alternativeID="RID_F03A",
    dssFilePath=Path("path/to/your/data.dss"),
    system=system
)

simulation.load_system_data()

# Create standardized plots
plotter = SimulationPlotter()
plot = plotter.plot_reservoir(simulation, "NBB")
plot.show()
```

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
- **`Reservoir`** - Physical reservoir with operational characteristics  
- **`TimeSeries`** - Core time series data structure

### Collections

- **`Operation`** - Groups related datasets for a reservoir operation
- **`System`** - Manages multiple reservoirs and downstream locations

### Simulation

- **`Simulation`** - Top-level orchestrator for loading and managing simulation data

### Plotting

- **`SimulationPlotter`** - Main interface for creating standardized plots
- **`ReservoirPlotter`** - Single reservoir visualization
- **`ComparisonPlotter`** - Multi-simulation comparison plots
- **`PlotConfig`** - Configuration for plot appearance and behavior

## DSS Integration

The package provides seamless integration with HEC-DSS files:

```python
# DSS paths are automatically constructed
# Format: //LOCATION/PARAMETER/DATE/TIMESTEP/SCENARIO/
dss_path = "//NEW BULLARDS BAR-POOL/STOR//1HOUR/C:000084|RID_F03A--0/"

# Data is loaded automatically when calling load_timeseries_from_dss()
reservoir.load_timeseries_from_dss(simulation)
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