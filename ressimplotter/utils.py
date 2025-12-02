

from ressimplotter.components.dataset import Dataset
from typing import Dict
from ressimplotter.collections.operation import Operation

def create_standard_reservoir_operation() -> Dict[str, Dataset]:
    """Create standard time series specifications."""
    return Operation( 
    operation_type="Standard",
    description="Standard reservoir operation",
    datasets=
    [
        Dataset(
            name="Elevation",
            parameter="ELEV", 
            # units="FEET",
        ),
        Dataset(
            name="Outflow",
            parameter="FLOW-OUT",
            # units="CFS", 
        ),
        Dataset(
            name="Inflow", 
            parameter="FLOW-IN",
            # units="CFS",
        ),
         Dataset(
            name="Storage",
            parameter="STOR",
            # units="AF",
        ),
        
    ]
    )

def create_firo_reservoir_timeseries() -> Dict[str, Dataset]:
    """Create standard time series specifications."""
    return [
        Dataset(
            name="Elevation",
            parameter="ELEV", 
            units="FEET",
        ),
        Dataset(
            name="Release",
            parameter="FLOW-OUT",
            units="CFS", 
        ),
        Dataset(
            name="Inflow", 
            parameter="FLOW-IN",
            units="CFS",
        ),
        Dataset(
            name="Storage",
            parameter="STOR",
            units="AF",
        ),
        Dataset(
            name="FIRO Target Elevation",
            parameter="ELEV-ZONE",
            units="ELEV",
        ),
        Dataset(
            name="FIRO Target Elevation",
            parameter="ELEV-ZONE",
            units="ELEV",
        ),
        
    ]


