from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import copy

from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.collections.system import System


@dataclass
class Simulation:
    """Represents a reservoir simulation run.

    A simulation binds run-time policies (``operations`` and ``zones``, keyed by
    reservoir short name) to the physical reservoirs it operates on. The physical
    reservoirs come from either ``system`` (multi-reservoir case) or the
    ``reservoirs`` list (single/ad-hoc case).
    """

    collectionID: int
    alternativeID: str
    dssFilePath: str | Path
    time_step: str = "1HOUR"
    trialID: Optional[str] = None

    # Physical topology (pick one). If both are provided, ``system`` wins.
    system: Optional[System] = None
    reservoirs: Optional[List[Reservoir]] = None
    downstream_locations: Optional[List[Dataset]] = None

    # Run-time policies, keyed by Reservoir.name
    operations: Dict[str, Operation] = field(default_factory=dict)
    zones: Dict[str, List[Dataset]] = field(default_factory=dict)

    def __str__(self):
        return (
            f"Simulation(collectionID={self.collectionID}, "
            f"alternativeID={self.alternativeID}, trialID={self.trialID})"
        )

    def build_fpart(self) -> str:
        """Build the F-part of a DSS path based on simulation identifiers."""
        if self.trialID is None:
            return f"C:{self.collectionID:06d}|{self.alternativeID}"
        return f"C:{self.collectionID:06d}|{self.alternativeID}--{self.trialID}"

    # ------------------------------------------------------------------
    # Topology accessors
    # ------------------------------------------------------------------
    def _own_reservoirs(self) -> List[Reservoir]:
        """Return the physical reservoirs this simulation operates on."""
        if self.system and self.system.reservoirs:
            return list(self.system.reservoirs)
        return list(self.reservoirs) if self.reservoirs else []

    def _own_downstream_locations(self) -> List[Dataset]:
        if self.system and self.system.downstream_locations:
            return list(self.system.downstream_locations)
        return list(self.downstream_locations) if self.downstream_locations else []

    def get_reservoir_by_name(self, name: str) -> Optional[Reservoir]:
        """Retrieve a reservoir by name from the simulation's topology."""
        for reservoir in self._own_reservoirs():
            if reservoir.name == name:
                return reservoir
        return None

    def get_all_downstream_location_names(self) -> List[str]:
        return [loc.name for loc in self._own_downstream_locations()]

    # ------------------------------------------------------------------
    # Run-time policy accessors
    # ------------------------------------------------------------------
    def get_operation(self, reservoir_name: str) -> Operation:
        """Return the ``Operation`` bound to ``reservoir_name`` for this run."""
        # Prefer independent copy (populated after load) so timeseries survive.
        op = self._loaded_operations().get(reservoir_name)
        if op is None:
            raise KeyError(
                f"No operation registered for reservoir '{reservoir_name}' "
                f"on simulation '{self.alternativeID}'. Available: "
                f"{list(self._loaded_operations().keys())}"
            )
        return op

    def get_zones(self, reservoir_name: str) -> List[Dataset]:
        """Return the list of zone ``Dataset``s bound to ``reservoir_name``."""
        return list(self._loaded_zones().get(reservoir_name, []))

    def _loaded_operations(self) -> Dict[str, Operation]:
        return getattr(self, "_operations_copy", None) or self.operations

    def _loaded_zones(self) -> Dict[str, List[Dataset]]:
        return getattr(self, "_zones_copy", None) or self.zones

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _create_independent_policy_copies(self):
        """Deep-copy per-reservoir policies (operations and zones) so each
        simulation gets its own dataset instances to hold loaded timeseries.
        Downstream locations are loaded in place because they are not shared
        across simulations the way operations typically are."""
        if not hasattr(self, "_operations_copy") or self._operations_copy is None:
            self._operations_copy = copy.deepcopy(self.operations)
        if not hasattr(self, "_zones_copy") or self._zones_copy is None:
            self._zones_copy = copy.deepcopy(self.zones)

    def load_downstream_location_data(self):
        """Load timeseries for all downstream locations."""
        for location in self._own_downstream_locations():
            location.load_timeseries_from_dss(self)

    def load_system_data(self):
        """Load timeseries for downstream locations and every registered
        reservoir operation and zone dataset."""
        self._create_independent_policy_copies()

        # Downstream locations (loaded in place, not deep-copied)
        for location in self._own_downstream_locations():
            location.load_timeseries_from_dss(self)

        # Reservoir operations + zones
        reservoirs_by_name = {r.name: r for r in self._own_reservoirs()}
        dss_file_path = Path(self.dssFilePath)
        fpart = self.build_fpart()

        for reservoir_name, operation in self._operations_copy.items():
            reservoir = reservoirs_by_name.get(reservoir_name)
            if reservoir is None:
                print(
                    f"Warning: operation registered for '{reservoir_name}' "
                    f"but no matching reservoir on simulation "
                    f"'{self.alternativeID}'. Skipping."
                )
                continue

            for dataset in operation.datasets:
                dataset.load_reservoir_timeseries_from_dss(
                    dss_file_path=dss_file_path,
                    reservoir_dss_code=reservoir.dss_location_code,
                    time_step=self.time_step,
                    fpart=fpart,
                )

        for reservoir_name, zone_datasets in self._zones_copy.items():
            if not zone_datasets:
                continue
            for zone_dataset in zone_datasets:
                if zone_dataset:
                    zone_dataset.load_timeseries_from_dss(self)
