"""
Plotting module for ResSimPlotter - standardized visualization from simulation objects.

This module provides a clean API for creating standardized plots from simulation data,
supporting both single simulation plots and multi-simulation comparisons.
"""

from typing import List, Dict, Tuple
import pandas as pd
import altair as alt
from abc import ABC, abstractmethod

from ressimplotter.simulation import Simulation

# Import plotting configurations
from ressimplotter.plotting.config import PlotConfig, SimulationStyle, ColorSchemes


class BasePlotter(ABC):
    """Abstract base class for all plotters."""
    
    def __init__(self, config: PlotConfig = None):
        self.config = config or PlotConfig()
        
    @abstractmethod
    def create_plot(self, *args, **kwargs) -> alt.Chart:
        """Create and return the plot."""
        pass
    
    def format_date_for_scale(self, date_value, format_str='%Y-%m-%d %H:%M'):
        """Format date for Altair scale domains."""
        return date_value.strftime(format_str)
    
    def _create_zone_rules_chart(self, start_date: str, end_date: str, 
                                zones: Dict[str, float], elev_range: Tuple[float, float]) -> alt.Chart:
        """Create zone reference lines chart."""
        zone_data = []
        for zone_name, elevation in zones.items():
            if elev_range[0] <= elevation <= elev_range[1]:  # Only show zones within range
                zone_data.extend([
                    {'datetime': start_date, 'elevation': elevation, 'zone': zone_name},
                    {'datetime': end_date, 'elevation': elevation, 'zone': zone_name}
                ])
        
        if not zone_data:
            # Return empty chart if no zones in range
            return alt.Chart(pd.DataFrame()).mark_line()
        
        zone_df = pd.DataFrame(zone_data)
        zone_df['datetime'] = pd.to_datetime(zone_df['datetime'])
        
        return alt.Chart(zone_df).mark_line(
            strokeDash=[8, 4], 
            stroke='black',
            strokeWidth=1,
            opacity=0.5
        ).encode(
            x=alt.X('datetime:T'),
            y=alt.Y('elevation:Q'),
            detail='zone:N'
        )
class ReservoirPlotter(BasePlotter):
    """Plotter for single reservoir visualization."""
    
    def create_plot(self, simulation: Simulation, reservoir_name: str) -> alt.Chart:
        """
        Create a plot for a single reservoir from a simulation.
        
        Args:
            simulation: The simulation object
            reservoir_name: Name of the reservoir to plot
            
        Returns:
            Combined elevation and flow plot
        """
        data = self.extract_reservoir_data(simulation, reservoir_name, include_zones=self.config.show_zones)
        
        # Create elevation plot
        elevation_plot = self._create_elevation_plot(data, simulation, reservoir_name)
        
        # Create flow plot
        flow_plot = self._create_flow_plot(data, simulation, reservoir_name)
        
        # Combine plots
        return alt.vconcat(elevation_plot, flow_plot).resolve_scale(
            x='shared', color='independent', strokeDash='independent'
        )
    
    def extract_reservoir_data(self, simulation: Simulation, reservoir_name: str,
                              include_zones: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Extract and prepare reservoir data for plotting. Also used by
        ``ComparisonPlotter`` to gather per-simulation series.

        Args:
            simulation: The simulation object
            reservoir_name: Name of the reservoir to extract data for
            include_zones: Whether to include zone data

        Returns:
            Dictionary with 'elevation', 'flow_in', 'flow_out', and optionally 'zones' DataFrames
        """
        reservoir = simulation.get_reservoir_by_name(reservoir_name)
        if not reservoir:
            raise ValueError(f"Reservoir '{reservoir_name}' not found in simulation")

        operation = simulation.get_operation(reservoir_name)
        zones = simulation.get_zones(reservoir_name)

        data: Dict[str, pd.DataFrame] = {}

        elev_df = operation.get_time_series_by_name("Elevation").to_dataframe_with_metadata()
        elev_df.loc[:, 'simulation'] = simulation.alternativeID
        data['elevation'] = elev_df

        flow_in_df = operation.get_time_series_by_name("Inflow").to_dataframe_with_metadata()
        flow_in_df.loc[:, 'simulation'] = simulation.alternativeID
        data['flow_in'] = flow_in_df

        try:
            flow_out_df = operation.get_time_series_by_name("Outflow").to_dataframe_with_metadata()
        except ValueError:
            flow_out_df = operation.get_time_series_by_name("Release").to_dataframe_with_metadata()
        flow_out_df.loc[:, 'simulation'] = simulation.alternativeID
        data['flow_out'] = flow_out_df

        if include_zones and zones:
            zones_list = [z.to_dataframe_with_metadata() for z in zones]
            zones_df = pd.concat(zones_list)
            zones_df.name = zones_df.name.str.replace(f"{reservoir.dss_location_code}-", "")
            zones_df.loc[:, 'simulation'] = simulation.alternativeID
            data['zones'] = zones_df

        return data
    
    def _create_elevation_plot(self, data: Dict[str, pd.DataFrame], 
                              simulation: Simulation, reservoir_name: str) -> alt.Chart:
        """Create elevation plot with zones."""
        # Combine elevation and zone data
        plot_data = [data['elevation']]
        if 'zones' in data:
            plot_data.append(data['zones'])
        
        merge = pd.concat(plot_data, ignore_index=True)
        
        # Get elevation range from config or auto-scale
        elev_range = self.config.elevation_range
        if elev_range is None:
            # Auto-scale based on data
            elev_range = (merge['value'].min() * 0.95, merge['value'].max() * 1.05)
        
        # Create interactive selection
        nearest = alt.selection_point(nearest=True, on="pointerover", fields=["datetime"], empty=False)
        
        # Get dynamic color mapping based on actual data
        unique_names = sorted(merge.groupby('name').name.first().to_list())
        colors = self._get_elevation_colors(unique_names)
        stroke_patterns = self._get_elevation_stroke_patterns(unique_names)
        
        # Main elevation plot
        plot = alt.Chart(merge).mark_line().encode(
            x=alt.X('datetime:T', title=None, axis=alt.Axis(format='%Y-%m-%d', labels=False)).scale(
                domain=[
                    self.format_date_for_scale(merge.datetime.min()),
                    self.format_date_for_scale(merge.datetime.max())
                ]
            ),
            y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elev_range),
            color=alt.Color('name:N', 
                          title='Legend' if self.config.show_legend else None, 
                          scale=alt.Scale(domain=unique_names, range=colors),
                          legend=alt.Legend(orient=self.config.legend_position) if self.config.show_legend else None),
            strokeDash=alt.StrokeDash('name:N', 
                                   scale=alt.Scale(domain=unique_names, range=stroke_patterns),
                                   legend=None)
        ).properties(
            title=self._get_title(reservoir_name, simulation),
            width=self.config.width,
            height=self.config.height
        )
        
        # Add zones if configured
        if self.config.show_zones and self.config.zone_elevations:
            zone_rules = self._create_zone_rules_chart(
                self.format_date_for_scale(merge.datetime.min()),
                self.format_date_for_scale(merge.datetime.max()),
                self.config.zone_elevations, 
                elev_range
            )
            plot = plot + zone_rules
        
        # Add interactive rules if configured
        if self.config.show_interactive_rules:
            rules = self._create_interactive_rules(merge, nearest)
            plot = plot + rules
        
        return plot.resolve_scale(color='shared')
    
    def _get_elevation_colors(self, names: List[str]) -> List[str]:
        """Get colors for elevation plot elements based on actual data names."""
        colors = []
        for name in names:
            # Check if name matches any known color scheme keys
            if name in ColorSchemes.ELEVATION_ZONES:
                colors.append(ColorSchemes.ELEVATION_ZONES[name])
            elif 'Elevation' in name or 'ELEV' in name:
                colors.append(ColorSchemes.ELEVATION_ZONES['Elevation'])
            else:
                # Default to zone color for unknown names
                colors.append('#7D7979')
        return colors
    
    def _get_elevation_stroke_patterns(self, names: List[str]) -> List[List[int]]:
        """Get stroke patterns for elevation plot elements."""
        patterns = []
        for name in names:
            if 'Elevation' in name or 'ELEV' in name:
                patterns.append([1, 0])  # Solid line for elevation
            else:
                patterns.append([4, 4])  # Dashed for zones
        return patterns
    
    def _create_flow_plot(self, data: Dict[str, pd.DataFrame], 
                         simulation: Simulation, reservoir_name: str) -> alt.Chart:
        """Create flow plot."""
        flow_df = pd.concat([data['flow_in'], data['flow_out']], ignore_index=True)
        
        # Create interactive selection
        nearest = alt.selection_point(nearest=True, on="pointerover", fields=["datetime"], empty=False)
        when_near = alt.when(nearest)
        
        plot = alt.Chart(flow_df).mark_line().encode(
            x=alt.X('datetime:T', title=None).axis(format='%Y-%m-%d').scale(
                domain=[
                    self.format_date_for_scale(flow_df.datetime.min()),
                    self.format_date_for_scale(flow_df.datetime.max())
                ]
            ),
            y=alt.Y('value:Q', title='Flow (cfs)').scale(
                domain=(0, round(flow_df.value.max() * 1.2, -4))
            ),
            color=alt.Color('parameter:N', 
                          title='Flow Type' if self.config.show_legend else None,
                          scale=alt.Scale(
                              domain=['FLOW-OUT', 'FLOW-IN'],
                              range=[ColorSchemes.FLOW_TYPES['OUTFLOW'], ColorSchemes.FLOW_TYPES['INFLOW']]
                          ),
                          legend=alt.Legend(orient=self.config.legend_position) if self.config.show_legend else None),
            strokeDash=alt.StrokeDash('parameter:N', 
                                   scale=alt.Scale(
                                       domain=['FLOW-OUT', 'FLOW-IN'],
                                       range=[[1,0], [4,4]]
                                   ),
                                   legend=None)
        ).properties(width=self.config.width, height=self.config.height)
        
        # Add interactive rules if configured
        if self.config.show_interactive_rules:
            rules = alt.Chart(flow_df).transform_pivot(
                "parameter", value="value", groupby=["datetime"]
            ).mark_rule(color="gray").encode(
                x="datetime:T",
                opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
                tooltip=[
                    alt.Tooltip(c, type="quantitative", format=",.0f") 
                    for c in ['FLOW-OUT', 'FLOW-IN']
                ] + [alt.Tooltip('datetime:T', type='temporal', format='%Y-%m-%d %H:%M')],
            ).add_params(nearest)
            plot = plot + rules
        
        return plot.resolve_scale(color='shared')
    
    def _create_zone_rules(self, merge: pd.DataFrame, elev_range: Tuple[int, int], 
                          reservoir_name: str) -> alt.Chart:
        """Create zone reference lines using config data."""
        if not self.config.zone_elevations:
            return alt.Chart(pd.DataFrame()).mark_line()  # Empty chart
            
        return self._create_zone_rules_chart(
            self.format_date_for_scale(merge.datetime.min()),
            self.format_date_for_scale(merge.datetime.max()),
            self.config.zone_elevations,
            elev_range
        )
    
    def _get_title(self, reservoir_name: str, simulation: Simulation) -> str:
        """Generate title including simulation info."""
        if self.config.title_include_simulation:
            reservoir_display_name = self.config.reservoir_full_name or reservoir_name
            return f"{reservoir_display_name} (simulation: {simulation.alternativeID})"
        else:
            return self.config.reservoir_full_name or reservoir_name
    
    def _create_interactive_rules(self, merge: pd.DataFrame, nearest) -> alt.Chart:
        """Create interactive hover rules."""
        when_near = alt.when(nearest)
        return alt.Chart(merge).transform_pivot(
            "name", value="value", groupby=["datetime"]
        ).mark_rule(color="gray", strokeWidth=2).encode(
            x="datetime:T",
            opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip(c, type="quantitative", format=".2f") 
                for c in sorted(merge.groupby('name').name.first().to_list())
            ] + [alt.Tooltip('datetime:T', type='temporal', format='%Y-%m-%d %H:%M')],
        ).add_params(nearest)


class ComparisonPlotter(BasePlotter):
    """Plotter for comparing multiple simulations."""
    
    def __init__(self, config: PlotConfig = None):
        super().__init__(config)
        self.simulation_styles = self._create_default_styles()

    def _get_title(self, reservoir_name: str, simulation: Simulation) -> str:
        """Generate title including simulation info."""
        if self.config.title_include_simulation:
            reservoir_display_name = self.config.reservoir_full_name or reservoir_name
            return f"{reservoir_display_name} (simulation: {simulation.alternativeID})"
        else:
            return self.config.reservoir_full_name or reservoir_name
    
    
    def _get_simulation_colors(self, alternative_sim: Simulation, baseline_sims: List[Simulation]) -> Dict[str, str]:
        """Get color mapping for simulations based on ColorSchemes."""
        color_mapping = {}
        
        # Alternative simulation gets the alternative color
        color_mapping[alternative_sim.alternativeID] = ColorSchemes.SIMULATION_COMPARISON['ALTERNATIVE']
        
        # Baseline simulations get sequential baseline colors
        baseline_color_keys = ['baseline_1', 'baseline_2', 'baseline_3', 'baseline_4']
        for i, sim in enumerate(baseline_sims):
            if i < len(baseline_color_keys):
                color_key = baseline_color_keys[i]
                color_mapping[sim.alternativeID] = ColorSchemes.SIMULATION_COMPARISON[color_key]
            else:
                # Fallback to gray if more baselines than defined colors
                color_mapping[sim.alternativeID] = '#7D7979'
        
        return color_mapping
    
    def _create_elevation_plot(self, simulation_data: List[Dict], 
                                     alternative_sim: Simulation, reservoir_name: str, 
                                     baseline_shortname: List[str] = None) -> alt.Chart:
        """Create unified elevation comparison plot using ReservoirPlotter logic."""
        # Create name mapping for simulations
        name_mapping = {}
        baseline_sims = [sd['simulation'] for sd in simulation_data if not sd['is_alternative']]
        
        # Map alternative simulation
        name_mapping[alternative_sim.alternativeID] = alternative_sim.alternativeID
        
        # Map baseline simulations with shortnames if provided
        for i, sim in enumerate(baseline_sims):
            if baseline_shortname and i < len(baseline_shortname):
                name_mapping[sim.alternativeID] = baseline_shortname[i]
            else:
                name_mapping[sim.alternativeID] = sim.alternativeID
        
        # Combine all elevation data
        all_elevation_data = []
        
        for sim_data in simulation_data:
            elev_df = sim_data['data']['elevation'].copy()
            # Use shortname for simulation column if provided
            elev_df['simulation'] = name_mapping[elev_df['simulation'].iloc[0]]
            elev_df['sim_type'] = 'alternative' if sim_data['is_alternative'] else 'baseline'
            all_elevation_data.append(elev_df)
            
            # Add zones for alternative simulation only
            if sim_data['is_alternative'] and 'zones' in sim_data['data']:
                zones_df = sim_data['data']['zones'].copy()
                zones_df['simulation'] = name_mapping[sim_data['simulation'].alternativeID]
                zones_df['sim_type'] = 'alternative'
                all_elevation_data.append(zones_df)
        
        combined_df = pd.concat(all_elevation_data, ignore_index=True)
        
        # Get elevation range
        elev_range = self.config.elevation_range
        if elev_range is None:
            elev_range = (combined_df['value'].min() * 0.95, combined_df['value'].max() * 1.05)
        
        # Create color mapping for display names
        display_name_colors = {}
        alt_display_name = name_mapping[alternative_sim.alternativeID]
        display_name_colors[alt_display_name] = ColorSchemes.SIMULATION_COMPARISON['ALTERNATIVE']
        
        baseline_color_keys = ['baseline_1', 'baseline_2', 'baseline_3', 'baseline_4']
        baseline_display_names = [name_mapping[sim.alternativeID] for sim in baseline_sims]
        
        for i, display_name in enumerate(baseline_display_names):
            if i < len(baseline_color_keys):
                color_key = baseline_color_keys[i]
                display_name_colors[display_name] = ColorSchemes.SIMULATION_COMPARISON[color_key]
            else:
                display_name_colors[display_name] = '#7D7979'
        
        # Create plot with mixed styling - simulation-based colors but name-based overrides for special series
        # Create interactive selection
        nearest = alt.selection_point(nearest=True, on="pointerover", fields=["datetime"], empty=False)
        
        # Create style_key using vectorized operations - much faster than row-by-row apply
        # Get all zone names from alternative simulation for special handling
        zone_names = set()
        alt_reservoir = alternative_sim.get_reservoir_by_name(reservoir_name)
        alt_zones = alternative_sim.get_zones(reservoir_name)
        if alt_reservoir and alt_zones:
            zone_names = {zone.name.replace(f"{alt_reservoir.dss_location_code}-", "") for zone in alt_zones if zone}
        
        # Create style_key: zones get their own name, simulations get simulation name
        combined_df['style_key'] = combined_df['simulation'].where(
            ~combined_df['name'].isin(zone_names),
            combined_df['name']
        )

        
        # Get unique style keys and create color/stroke mappings
        unique_style_keys = sorted(combined_df['style_key'].unique())
        style_colors = []
        style_strokes = []
        
        for style_key in unique_style_keys:
            if style_key in zone_names:
                # Zone gets its color from ColorSchemes and dashed line
                if style_key in ColorSchemes.ELEVATION_ZONES:
                    style_colors.append(ColorSchemes.ELEVATION_ZONES[style_key])
                else:
                    style_colors.append('#000000')  # Default black for unknown zones
                style_strokes.append([4, 4])
            elif style_key == name_mapping[alternative_sim.alternativeID]:
                # Alternative simulation gets solid line and alternative color
                style_colors.append(display_name_colors[style_key])
                style_strokes.append([1, 0])
            else:
                # Baseline simulations get dashed line and baseline color
                style_colors.append(display_name_colors[style_key])
                style_strokes.append([1,0])
        
        plot = alt.Chart(combined_df).mark_line().encode(
            x=alt.X('datetime:T', title=None).axis(format='%Y-%m-%d', labels=True),
            y=alt.Y('value:Q', title='Elevation (ft)').scale(domain=elev_range),
            color=alt.Color('style_key:N', 
                          title=None,
                          scale=alt.Scale(domain=unique_style_keys, range=style_colors),
                          legend=alt.Legend(orient=self.config.legend_position,
                                          )),
            strokeDash=alt.StrokeDash('style_key:N',
                                   scale=alt.Scale(domain=unique_style_keys, range=style_strokes)),
        ).properties(
            title=self._get_title(reservoir_name, alternative_sim),
            width=self.config.width,
            height=self.config.height
        )
        
        # Add zones if configured
        if self.config.show_zones and self.config.zone_elevations:
            zone_rules = self._create_zone_rules_chart(
                self.format_date_for_scale(combined_df.datetime.min()),
                self.format_date_for_scale(combined_df.datetime.max()),
                self.config.zone_elevations, 
                elev_range
            )
            plot = plot + zone_rules
        
        # Add interactive rules if configured
        if self.config.show_interactive_rules:
            rules = self._create_interactive_rules_comparison(combined_df, nearest)
            plot = plot + rules
        
        return plot
    
    def _create_interactive_rules_comparison(self, combined_df: pd.DataFrame, nearest) -> alt.Chart:
        """Create interactive hover rules for comparison plots."""
        when_near = alt.when(nearest)
        return alt.Chart(combined_df).transform_pivot(
            "style_key", value="value", groupby=["datetime"]
        ).mark_rule(color="gray", strokeWidth=2).encode(
            x="datetime:T",
            opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip(c, type="quantitative", format=",.2f") 
                for c in sorted(combined_df['style_key'].unique())
            ] + [
                alt.Tooltip('datetime:T', type='temporal', format='%Y-%m-%d %H:%M')
            ],
        ).add_params(nearest)
    
    def _create_interactive_rules_flow_comparison(self, combined_df: pd.DataFrame, nearest) -> alt.Chart:
        """Create interactive hover rules for flow comparison plots."""
        when_near = alt.when(nearest)
        return alt.Chart(combined_df).transform_pivot(
            "style_key", value="value", groupby=["datetime"]
        ).mark_rule(color="gray", strokeWidth=2).encode(
            x="datetime:T",
            opacity=when_near.then(alt.value(0.3)).otherwise(alt.value(0)),
            tooltip=[
                alt.Tooltip(c, type="quantitative", format=",.0f") 
                for c in sorted(combined_df['style_key'].unique())
            ] + [
                alt.Tooltip('datetime:T', type='temporal', format='%Y-%m-%d %H:%M')
            ],
        ).add_params(nearest)
    
    def _create_flow_plot(self, simulation_data: List[Dict], 
                                alternative_sim: Simulation, reservoir_name: str,
                                baseline_shortname: List[str] = None) -> alt.Chart:
        """Create unified flow comparison plot using ReservoirPlotter logic."""
        # Create name mapping for simulations
        name_mapping = {}
        baseline_sims = [sd['simulation'] for sd in simulation_data if not sd['is_alternative']]
        
        # Map alternative simulation
        name_mapping[alternative_sim.alternativeID] = alternative_sim.alternativeID
        
        # Map baseline simulations with shortnames if provided
        for i, sim in enumerate(baseline_sims):
            if baseline_shortname and i < len(baseline_shortname):
                name_mapping[sim.alternativeID] = baseline_shortname[i]
            else:
                name_mapping[sim.alternativeID] = sim.alternativeID
        
        # Combine all flow data
        all_flow_data = []
        
        for sim_data in simulation_data:
            # For baseline simulations, only include FLOW-OUT; for alternative, include both
            if sim_data['is_alternative']:
                flow_df = pd.concat([sim_data['data']['flow_in'], sim_data['data']['flow_out']], ignore_index=True)
            else:
                flow_df = sim_data['data']['flow_out'].copy()
            
            # Use shortname for simulation column if provided
            flow_df['simulation'] = name_mapping[flow_df['simulation'].iloc[0]]
            flow_df['sim_type'] = 'alternative' if sim_data['is_alternative'] else 'baseline'
            
            # Create unified style_key for flow using vectorized operations - much faster than row-by-row apply
            if sim_data['is_alternative']:
                # Alternative: FLOW-OUT uses simulation name, FLOW-IN uses 'FLOW-IN'
                flow_df['style_key'] = flow_df['simulation'].where(
                    flow_df['parameter'] == 'FLOW-OUT',
                    'FLOW-IN'
                )
            else:
                # Baseline: all flows use simulation name
                flow_df['style_key'] = flow_df['simulation']
            all_flow_data.append(flow_df)
        
        combined_df = pd.concat(all_flow_data, ignore_index=True)
        
        # Create color mapping for display names
        display_name_colors = {}
        alt_display_name = name_mapping[alternative_sim.alternativeID]
        display_name_colors[alt_display_name] = ColorSchemes.SIMULATION_COMPARISON['ALTERNATIVE']
        
        baseline_color_keys = ['baseline_1', 'baseline_2', 'baseline_3', 'baseline_4']
        baseline_display_names = [name_mapping[sim.alternativeID] for sim in baseline_sims]
        
        for i, display_name in enumerate(baseline_display_names):
            if i < len(baseline_color_keys):
                color_key = baseline_color_keys[i]
                display_name_colors[display_name] = ColorSchemes.SIMULATION_COMPARISON[color_key]
            else:
                display_name_colors[display_name] = '#7D7979'
        
        # Create color and stroke mapping based on style_key
        unique_style_keys = sorted(combined_df['style_key'].unique())
        
        # Create color mapping for flow style keys
        style_colors = []
        style_strokes = []
        
        for style_key in unique_style_keys:
            if style_key == 'FLOW-IN':
                # FLOW-IN gets inflow color and dashed line
                style_colors.append(ColorSchemes.FLOW_TYPES['INFLOW'])
                style_strokes.append([4, 4])
            elif style_key == name_mapping[alternative_sim.alternativeID]:
                # Alternative simulation FLOW-OUT gets alternative color and solid line
                style_colors.append(display_name_colors[style_key])
                style_strokes.append([1, 0])
            else:
                # Baseline simulations get baseline color and solid line
                style_colors.append(display_name_colors[style_key])
                style_strokes.append([1, 0])
        
        colors = style_colors
        
        # Create interactive selection
        nearest = alt.selection_point(nearest=True, on="pointerover", fields=["datetime"], empty=False)
        
        plot = alt.Chart(combined_df).mark_line().encode(
            x=alt.X('datetime:T', title=None).axis(format='%Y-%m-%d', labels=True),
            y=alt.Y('value:Q', title='Flow (cfs)'),
            color=alt.Color('style_key:N', 
                          title=None,
                          scale=alt.Scale(domain=unique_style_keys, range=colors),
                          legend=alt.Legend(orient=self.config.legend_position)),
            strokeDash=alt.StrokeDash('style_key:N',
                                   scale=alt.Scale(domain=unique_style_keys, range=style_strokes))
        ).properties(
            width=self.config.width,
            height=self.config.height
        )
        
        # Add interactive rules if configured
        if self.config.show_interactive_rules:
            rules = self._create_interactive_rules_flow_comparison(combined_df, nearest)
            plot = plot + rules
        
        return plot
    
    def create_plot(self, alternative_simulation: Simulation, 
                   baseline_simulations: List[Simulation],
                   reservoir_name: str,
                   baseline_shortname: List[str] = None) -> alt.Chart:
        """
        Create a comparison plot between alternative and baseline simulations.
        
        Args:
            alternative_simulation: The simulation being tested (shows all details)
            baseline_simulations: List of baseline simulations (simplified view)
            reservoir_name: Name of the reservoir to compare
            baseline_shortname: List of short names for baseline simulations in legend
            
        Returns:
            Combined comparison plot
        """
        all_simulations = [alternative_simulation] + baseline_simulations
        
        # Create a ReservoirPlotter instance to leverage its data extraction and processing
        reservoir_plotter = ReservoirPlotter(self.config)
        
        # Extract data for all simulations using ReservoirPlotter's method
        simulation_data = []
        for i, sim in enumerate(all_simulations):
            is_alternative = (i == 0)
            data = reservoir_plotter.extract_reservoir_data(
                sim, reservoir_name, include_zones=is_alternative and self.config.show_zones
            )
            simulation_data.append({
                'simulation': sim,
                'data': data,
                'is_alternative': is_alternative
            })
        
        # Create unified comparison plots
        elevation_plot = self._create_elevation_plot(simulation_data, alternative_simulation, reservoir_name, baseline_shortname)
        flow_plot = self._create_flow_plot(simulation_data, alternative_simulation, reservoir_name, baseline_shortname)
        
        return alt.vconcat(elevation_plot, flow_plot).resolve_scale(
           x='shared', color='independent', strokeDash='independent'
        )

    
    def _create_default_styles(self) -> Dict[str, SimulationStyle]:
        """Create default styling for different simulation types."""
        return {
            'alternative': SimulationStyle(
                name='Alternative',
                color='#d7191c',
                stroke_dash=[1, 0],
                opacity=1.0,
                is_baseline=False
            ),
            'baseline': SimulationStyle(
                name='Baseline', 
                color='#7D7979',
                stroke_dash=[4, 4],
                opacity=0.7,
                is_baseline=True
            )
        }


class SimulationPlotter:
    """Main interface for creating standardized plots from simulation objects."""
    
    def __init__(self, config: PlotConfig = None):
        self.config = config or PlotConfig()
    
    def plot_reservoir(self, simulation: Simulation, reservoir_name: str, 
                      config: PlotConfig = None) -> alt.Chart:
        """
        Plot a single reservoir from a simulation.
        
        Args:
            simulation: The simulation object
            reservoir_name: Name of reservoir to plot
            config: Optional plot configuration
            
        Returns:
            Combined elevation and flow plot
        """
        plotter = ReservoirPlotter(config or self.config)
        return plotter.create_plot(simulation, reservoir_name)
    
    def plot_comparison(self, alternative_simulation: Simulation,
                       baseline_simulations: List[Simulation],
                       baseline_shortname: List[str],
                       reservoir_name: str,
                       config: PlotConfig = None) -> alt.Chart:
        """
        Plot comparison between alternative and baseline simulations.
        
        Args:
            alternative_simulation: The simulation being tested
            baseline_simulations: List of baseline simulations
            reservoir_name: Name of reservoir to compare
            config: Optional plot configuration
            
        Returns:
            Comparison plot
        """
        plotter = ComparisonPlotter(config or self.config)
        return plotter.create_plot(alternative_simulation, baseline_simulations, reservoir_name, baseline_shortname)
    
    def plot_system_overview(self, simulation: Simulation, 
                           config: PlotConfig = None) -> alt.Chart:
        """
        Plot overview of entire system from a simulation.
        
        Args:
            simulation: The simulation object
            config: Optional plot configuration
            
        Returns:
            System overview plot
        """
        # Implementation for system-wide plotting
        # This would create plots for all reservoirs and downstream locations
        pass