from dataclasses import dataclass


@dataclass
class Reservoir:
    """
    Physical description of a reservoir.

    Operations (which time series to load for a run) and time-varying zones
    (e.g. FIRO target curves) are run-time policies and live on the
    ``Simulation`` object, keyed by ``Reservoir.name``. Static horizontal
    reference elevations (top of dam, spillway crest, etc.) are drawn via
    ``PlotConfig.zone_elevations``. Plot axis domains live on ``PlotConfig``
    (``elevation_range``), not here.
    """
    name: str                                              # Short name (e.g., "ORO", "NBB")
    full_name: str                                         # Full name (e.g., "Oroville")
    dss_location_code: str                                 # DSS B-part identifier

    def __str__(self):
        return (
            f"Reservoir(name={self.name}, full_name={self.full_name}, "
            f"dss_location_code={self.dss_location_code})"
        )
