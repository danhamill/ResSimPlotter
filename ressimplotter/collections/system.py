from dataclasses import dataclass
from typing import List, Optional
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.components.dataset import Dataset

@dataclass
class System:
    """
    Top-level system configuration containing reservoirs, locations, and DSS file info.
    """
    name: str                                      # System name
    reservoirs: List[Reservoir]                   # List of reservoirs
    downstream_locations: List[Dataset]           # Downstream control points
    base_study_name: str = ""                     # Base study identifier for DSS paths
    
    def __str__(self):
        return f"System(name={self.name}, reservoirs={[res.name for res in self.reservoirs]}, downstream_locations={[loc.name for loc in self.downstream_locations]})"
    
    def get_reservoir_by_name(self, name: str) -> Optional[Reservoir]:
        """Get a reservoir by its name."""
        for reservoir in self.reservoirs:
            if reservoir.name == name:
                return reservoir
        return None
    
    def get_downstream_location_by_name(self, name: str) -> Optional[Dataset]:
        """Get a downstream location by name."""
        for location in self.downstream_locations:
            if location.name == name:
                return location
        return None
    
    def get_all_reservoir_names(self) -> List[str]:
        """Get list of all reservoir names."""
        return [res.name for res in self.reservoirs]
    
    def get_all_downstream_location_names(self) -> List[str]:
        """Get list of all downstream location names."""
        return [loc.name for loc in self.downstream_locations]