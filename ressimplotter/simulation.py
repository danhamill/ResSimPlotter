from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import copy

from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.system import System


@dataclass
class Simulation:

    """Class for representing a reservoir simulation."""
    collectionID: int
    alternativeID: str
    dssFilePath: str | Path
    time_step: str = "1HOUR"
    trialID: Optional[str] = None
    downstream_locations: Optional[List[Dataset]] = None # Downstream control points
    reservoirs: Optional[List[Reservoir]] = None                   # List of reservoirs
    system: Optional[System] = None  # System object - using Any to avoid circular import

    def __str__(self):
        return f"Simulation(collectionID={self.collectionID}, alternativeID={self.alternativeID}, trialID={self.trialID})"
    
    def build_fpart(self) -> str:
        """Build the F-part of a DSS path based on simulation identifiers."""
        # Example F-part format: "C:000001|RID_F03A--0"

        if self.trialID is None:
            return f"C:{self.collectionID:06d}|{self.alternativeID}"
        else:
            return f"C:{self.collectionID:06d}|{self.alternativeID}--{self.trialID}"
    def load_downstream_location_data(self):
        """Load simulation data from the DSS file for all downstream locations."""
        # Load timeseries data for each downstream location
        for location in self.downstream_locations:
            location.load_timeseries_from_dss(self)
    
    def get_all_downstream_location_names(self) -> List[str]:
        """Get names of all downstream locations."""
        return [location.name for location in self.downstream_locations]
    
    def get_reservoir_by_name(self, name: str) -> Optional[Reservoir]:
        """Retrieve a reservoir by its name from the independent system copy."""
        # Use independent system if data has been loaded, otherwise use original
        system_to_use = getattr(self, '_independent_system', None) or self.system
        
        if system_to_use and system_to_use.reservoirs:
            for reservoir in system_to_use.reservoirs:
                if reservoir.name == name:
                    return reservoir
        return None
    
    def _create_independent_system_copy(self):
        """Create an independent copy of the system with separate dataset instances."""
        if not hasattr(self, '_independent_system') or self._independent_system is None:
            # Create a deep copy of the system to avoid shared references
            self._independent_system = copy.deepcopy(self.system)
        return self._independent_system
    
    def load_system_data(self):
        """Load data for the entire system including downstream locations and reservoirs."""
        if self.system:
            # Use independent system copy to avoid shared dataset references
            independent_system = self._create_independent_system_copy()
            
            # Load downstream location data
            for location in independent_system.downstream_locations:
                location.load_timeseries_from_dss(self)
            
            # Load reservoir data if needed
            for reservoir in independent_system.reservoirs:
                for dataset in reservoir.operation.datasets:
                    dataset.load_reservoir_timeseries_from_dss(
                        dss_file_path=Path(self.dssFilePath),
                        reservoir_dss_code=reservoir.dss_location_code,
                        time_step=self.time_step,
                        fpart=self.build_fpart()
                    )
                    
                if reservoir.zones:
                    for zone_dataset in reservoir.zones:
                        if zone_dataset:
                            zone_dataset.load_timeseries_from_dss(self)
                    
                    
