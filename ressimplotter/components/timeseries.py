from dataclasses import dataclass
from typing import Optional
from hecdss.dsspath import DssPath

@dataclass
class TimeSeries:
    """
    Represents a time series data set for reservoir operations.
    """
    name: str                           # Time series name (e.g., "FLOW-IN", "FLOW-OUT")
    units: str                          # Units of measurement (e.g., "cfs", "acre-feet")
    parameter: str                      # DSS C-part identifier
    timeStep: str = '1HOUR'             # Time step (e.g., "1DAY", "1HOUR")
    path: Optional[str | DssPath] = None       # DSS path (to be constructed)
    data: Optional[list] = None                # Time series data loaded from DSS
    simulation_id: Optional[str] = None        # Reference to simulation (instead of object)
    
    
    def __str__(self):
        return f"TimeSeries(name={self.name}, units={self.units}, parameter={self.parameter}, timeStep={self.timeStep}, path={self.path})"
    def build_dss_path(self, basin: str, location: str, **path_kwargs) -> str:
        """Build a DSS path for this time series."""
        # DSS path format: /A/B/C/D/E/F/ where:
        # A = basin, B = location, C = parameter, D = start date, E = time step, F = version
        path_components = [
            f"/{basin}",
            f"/{location}",
            f"/{self.parameter}",
            "",  # D-part (start date) - typically empty for templates
            f"/{self.timeStep}"
        ]
        for key, value in path_kwargs.items():
            path_components.append(f"/{value}")
        
        return "".join(path_components) + "/"