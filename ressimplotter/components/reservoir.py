from dataclasses import dataclass
from typing import List, Optional, Tuple
from ressimplotter.collections.operation import Operation
from pathlib import Path


@dataclass
class Reservoir:
    """
    Represents a reservoir with its operations and characteristics.
    """
    name: str                           # Short name (e.g., "ORO", "NBB")
    full_name: str                      # Full name (e.g., "Oroville")
    dss_location_code: str             # DSS B-part identifier
    operation: Operation
    zones: Optional[List] = None  # Operational zones as list of Dataset objects
    flow_range: Optional[Tuple[float, float]] = None  # Min/max flow range
    elevation_range: Optional[Tuple[float, float]] = None  # Min/max elevation range


    def __str__(self):
        return f"Reservoir(name={self.name}, full_name={self.full_name}, dss_location_code={self.dss_location_code}, operations={self.operation})"

    def load_timeseries_from_dss(self, simulation) -> None:
        """Load all time series data for this reservoir from the DSS file."""
        if not self.operation:
            return
        
        # Extract needed values from simulation
        dss_file_path = Path(simulation.dssFilePath)
        time_step = simulation.time_step
        fpart = simulation.build_fpart()
        
        for dataset in self.operation.datasets:
            dataset.load_reservoir_timeseries_from_dss(
                dss_file_path=dss_file_path,
                reservoir_dss_code=self.dss_location_code,
                time_step=time_step,
                fpart=fpart
            )

        if self.zones:
            self.load_zone_datasets_from_dss(simulation)

    def load_zone_datasets_from_dss(self, simulation) -> None:
        """Load time series data for all zone datasets from the DSS file."""
        if not self.zones:
            print(f"No zones defined for reservoir {self.name}")
            return
        
        # Extract needed values from simulation
        
        print(f"Loading zone datasets for reservoir {self.name}")
        
        self.validate_zones()

        for zone_dataset in self.zones:
            if zone_dataset:
                zone_dataset.load_timeseries_from_dss(
                    simulation
                )

    def validate_zones(self) -> bool:
        """Validate that all zones belong to this reservoir."""
        if not self.zones:
            return True
        
        for zone in self.zones:
            if not zone.name.startswith(self.dss_location_code):
                raise ValueError(f"Zone '{zone.name}' does not match reservoir '{self.dss_location_code}'")
        return True
    

    def get_zone_datasets_plot(self):

        if not self.zones:
            return None
        
        dataframes = []
        for zone in self.zones:
            tmp = zone.to_dataframe_with_metadata()
            dataframes.append(tmp)

        return dataframes