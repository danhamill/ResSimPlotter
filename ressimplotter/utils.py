from ressimplotter.components.dataset import Dataset
from ressimplotter.collections.operation import Operation


def create_standard_reservoir_operation() -> Operation:
    """Standard reservoir operation: pool elevation, in/out flow, storage."""
    return Operation(
        operation_type="Standard",
        description="Standard reservoir operation",
        datasets=[
            Dataset(name="Elevation", parameter="ELEV"),
            Dataset(name="Outflow", parameter="FLOW-OUT"),
            Dataset(name="Inflow", parameter="FLOW-IN"),
            Dataset(name="Storage", parameter="STOR"),
        ],
    )


def create_firo_reservoir_operation() -> Operation:
    """FIRO reservoir operation. Same pool time series as the standard op;
    the FIRO target elevation is a zone, not an operation dataset, and should
    be registered separately in ``Simulation.zones``."""
    return Operation(
        operation_type="FIRO",
        description="FIRO reservoir operation",
        datasets=[
            Dataset(name="Elevation", parameter="ELEV"),
            Dataset(name="Release", parameter="FLOW-OUT"),
            Dataset(name="Inflow", parameter="FLOW-IN"),
            Dataset(name="Storage", parameter="STOR"),
        ],
    )
