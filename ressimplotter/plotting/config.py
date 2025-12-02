"""
Configuration and styling presets for the plotting module.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class PlotConfig:
    """Configuration for plot styling and behavior."""
    width: int = 600
    height: int = 300
    show_zones: bool = True
    show_interactive_rules: bool = True
    show_legend: bool = True
    legend_position: str = 'right'
    title_include_simulation: bool = True
    
    # Optional simulation-specific data
    elevation_range: Optional[Tuple[float, float]] = None  # (min, max) elevation for Y-axis
    reservoir_full_name: Optional[str] = None  # Full reservoir name for titles
    zone_elevations: Optional[Dict[str, float]] = None  # Zone elevations for overlays


@dataclass
class SimulationStyle:
    """Styling configuration for different simulation types."""
    name: str
    color: str
    stroke_dash: List[int]
    opacity: float = 1.0
    stroke_width: int = 2
    is_baseline: bool = False

class PlotPresets:
    """Predefined plot configurations for common use cases."""
    
    @staticmethod
    def detailed_analysis() -> PlotConfig:
        """Configuration for detailed analysis plots (shows everything)."""
        return PlotConfig(
            width=800,
            height=400,
            show_zones=True,
            show_interactive_rules=True,
            show_legend=True,
            legend_position='right',
            title_include_simulation=True
        )
    
    @staticmethod
    def presentation() -> PlotConfig:
        """Configuration for presentation plots (clean, high-level).""" 
        return PlotConfig(
            width=1000,
            height=300,
            show_zones=False,
            show_interactive_rules=False,
            show_legend=True,
            legend_position='right',
            title_include_simulation=False
        )
    
    @staticmethod
    def comparison() -> PlotConfig:
        """Configuration optimized for comparing multiple simulations."""
        return PlotConfig(
            width=900,
            height=350,
            show_zones=True,  # Only for alternative simulation
            show_interactive_rules=True,
            show_legend=True,
            legend_position='right',
            title_include_simulation=True
        )
    
    @staticmethod
    def dashboard() -> PlotConfig:
        """Configuration for dashboard/overview plots."""
        return PlotConfig(
            width=600,
            height=250,
            show_zones=False,
            show_interactive_rules=False,
            show_legend=False,
            legend_position='bottom',
            title_include_simulation=False
        )

class ColorSchemes:
    """Predefined color schemes for different plot types."""
    
    ELEVATION_ZONES = {
        'Elevation': '#d7191c',  # Red for main simulation
        'FLOOD CONTROL': '#7D7979',  # Gray for zones
        'FIRO TARGET': '#7D7979',
        'FIRO SPACE': '#7D7979', 
        'BELOW FIRO SPACE': '#7D7979'
    }
    
    FLOW_TYPES = {
        'INFLOW': '#7D7979',  # Gray for inflow
        'OUTFLOW': '#d7191c'  # Red for outflow
    }
    
    SIMULATION_COMPARISON = {
        'ALTERNATIVE': '#d7191c',  # Red for alternative
        'baseline_1': '#1f78b4',   # Blue for first baseline
        'baseline_2': '#33a02c',   # Green for second baseline
        'baseline_3': '#ff7f00',   # Orange for third baseline
        'baseline_4': '#6a3d9a'    # Purple for fourth baseline
    }

class StyleTemplates:
    """Templates for different types of plots."""
    
    @staticmethod
    def get_reservoir_analysis_template() -> Dict:
        """Get template for detailed reservoir analysis."""
        return {
            'config': PlotPresets.detailed_analysis(),
            'colors': ColorSchemes.ELEVATION_ZONES,
            'description': 'Detailed reservoir analysis with all zones and interactive features'
        }
    
    @staticmethod
    def get_comparison_template() -> Dict:
        """Get template for simulation comparisons."""
        return {
            'config': PlotPresets.comparison(),
            'colors': ColorSchemes.SIMULATION_COMPARISON,
            'description': 'Multi-simulation comparison optimized for baseline vs alternative'
        }
    
    @staticmethod
    def get_presentation_template() -> Dict:
        """Get template for presentations."""
        return {
            'config': PlotPresets.presentation(),
            'colors': ColorSchemes.ELEVATION_ZONES,
            'description': 'Clean presentation plots without clutter'
        }

# Usage examples in docstring
"""
Usage Examples:
==============

# Basic configuration (Altair auto-scales)
config = PlotPresets.detailed_analysis()
plotter = SimulationPlotter(config)

# Configuration with simulation-specific data
nbb_config = PlotConfig(
    width=800,
    height=400,
    show_zones=True,
    elevation_range=(1800, 2000),  # NBB elevation range
    reservoir_full_name='New Bullards Bar',
    zone_elevations={
        'flood_control': 1965,
        'top_conservation': 1955,
        'surcharge': 1975,
        'top_of_dam': 1995
    }
)

# Configuration without elevation range (auto-scale)
auto_config = PlotConfig(
    width=600,
    height=300,
    show_zones=True,
    # elevation_range=None,  # Let Altair determine scale
    reservoir_full_name='Oroville',
    zone_elevations={
        'flood_control': 850,
        'top_conservation': 900
    }
)

# Use a style template
template = StyleTemplates.get_comparison_template()
plotter = SimulationPlotter(template['config'])
"""