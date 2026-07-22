from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import copy

from ressimplotter.components.dataset import Dataset
from ressimplotter.components.reservoir import Reservoir
from ressimplotter.collections.operation import Operation
from ressimplotter.collections.system import System
from ressimplotter.dss_integration import (
    DSSReader,
    DSSLoadError,
    DSSPathNotFound,
)


@dataclass
class LoadReport:
    """Structured result of a ``Simulation.load_system_data`` call.

    Attributes are populated whether or not ``strict=True``. Use ``ok`` to
    check success and ``format()`` to render a human-readable summary.
    """
    simulation_id: str
    dss_file: str
    successes: List[str] = field(default_factory=list)
    missing_paths: List[Tuple[str, str]] = field(default_factory=list)   # (dataset_name, dss_path)
    read_errors: List[Tuple[str, str, str]] = field(default_factory=list)  # (dataset_name, dss_path, msg)
    missing_reservoirs: List[str] = field(default_factory=list)
    fpart_missing: Optional[str] = None
    similar_fparts: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_paths
            or self.read_errors
            or self.missing_reservoirs
            or self.fpart_missing
        )

    def format(self) -> str:
        lines = [f"Load failures for simulation {self.simulation_id}",
                 f"  DSS file: {self.dss_file}"]
        if self.fpart_missing:
            lines.append(f"  F-part '{self.fpart_missing}' not found in DSS catalog.")
            if self.similar_fparts:
                lines.append("  Similar F-parts present:")
                for fp in self.similar_fparts:
                    lines.append(f"    {fp}")
            lines.append("  Hint: check collectionID / alternativeID / trialID for typos.")
        if self.missing_reservoirs:
            lines.append("  Operations registered for reservoirs not in the system:")
            for name in self.missing_reservoirs:
                lines.append(f"    {name}")
        if self.missing_paths:
            lines.append(f"  Missing DSS paths ({len(self.missing_paths)}):")
            for name, path in self.missing_paths:
                lines.append(f"    [{name}] {path}")
        if self.read_errors:
            lines.append(f"  Read errors ({len(self.read_errors)}):")
            for name, path, msg in self.read_errors:
                lines.append(f"    [{name}] {path} -> {msg}")
        return "\n".join(lines)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise DSSLoadError(self.format(), simulation_id=self.simulation_id)


@dataclass
class Simulation:
    """Represents a reservoir simulation run.

    A simulation binds run-time policies (``operations`` and ``zones``, keyed by
    reservoir short name) to the physical reservoirs it operates on. The physical
    reservoirs come from either ``system`` (the normal case, shared across
    simulations) or the ad-hoc ``reservoirs`` / ``downstream_locations`` fields
    (one-off simulations that do not need a full ``System`` object).

    Topology selection rules:
      - If ``system`` is set, its reservoirs and downstream locations are used
        and the ad-hoc fields are ignored.
      - Otherwise the ad-hoc ``reservoirs`` and ``downstream_locations`` lists
        are used directly.

    Prefer ``system`` whenever more than one simulation shares the same
    topology; the ad-hoc fields exist for scripts and tests that build a
    single throwaway simulation without ceremony.
    """

    collectionID: int
    alternativeID: str
    dssFilePath: str | Path
    time_step: str = "1HOUR"
    trialID: Optional[str] = None

    # Physical topology. Prefer ``system`` for multi-simulation runs; use the
    # ad-hoc lists below only for one-off simulations. If ``system`` is set it
    # wins and the ad-hoc fields are ignored.
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
        """Load timeseries for downstream locations only.

        This is a targeted helper for simulations that were built without
        ``operations``/``zones`` (typically ad-hoc simulations using the
        ``reservoirs``/``downstream_locations`` fields). For the normal case
        prefer ``load_system_data``, which also loads downstream locations
        alongside every reservoir operation and zone dataset.

        Fails loudly on the first missing DSS file/path or read error; there is
        no ``strict=False`` mode here because the surface is intentionally
        small.
        """
        for location in self._own_downstream_locations():
            location.load_timeseries_from_dss(self)

    def load_system_data(self, *, strict: bool = True, preflight: bool = True) -> "LoadReport":
        """Load timeseries for downstream locations and every registered
        reservoir operation and zone dataset.

        Args:
            strict: If True (default), raise ``DSSLoadError`` when any dataset
                fails to load. Set False for batch runs where you'd rather
                collect failures across many simulations.
            preflight: If True (default), check the DSS catalog for this
                simulation's F-part before attempting any per-dataset loads.
                A missing F-part almost always indicates a typo in
                ``alternativeID``/``collectionID``/``trialID``; catching it
                once up-front produces a much clearer error than N per-path
                failures.

        Returns:
            LoadReport describing successes and failures. When ``strict`` is
            True and any failure occurred, the report is raised as a
            ``DSSLoadError`` instead of returned.
        """
        self._create_independent_policy_copies()

        dss_file_path = Path(self.dssFilePath)
        fpart = self.build_fpart()
        report = LoadReport(simulation_id=str(self), dss_file=str(dss_file_path))

        # File-level check first — no point continuing if the file is missing.
        if not dss_file_path.exists():
            report.read_errors.append(("<file>", str(dss_file_path), "DSS file not found"))
            if strict:
                report.raise_if_failed()
            return report

        # F-part preflight: fastest way to detect a typo in the simulation IDs.
        if preflight:
            try:
                reader = DSSReader(dss_file_path)
                fparts = reader.get_fparts()
                if fparts and fpart not in fparts:
                    report.fpart_missing = fpart
                    report.similar_fparts = self._suggest_similar_fparts(fpart, fparts)
                    if strict:
                        report.raise_if_failed()
                    return report
            except Exception as e:
                # Catalog reads shouldn't be fatal on their own — fall through
                # to the per-dataset loads which will surface any real issue.
                report.read_errors.append(("<catalog>", "", f"catalog read failed: {e}"))

        # Downstream locations (loaded in place, not deep-copied)
        for location in self._own_downstream_locations():
            self._safe_load(lambda loc=location: loc.load_timeseries_from_dss(self),
                            dataset_name=location.name, report=report)

        # Reservoir operations
        reservoirs_by_name = {r.name: r for r in self._own_reservoirs()}
        for reservoir_name, operation in self._operations_copy.items():
            reservoir = reservoirs_by_name.get(reservoir_name)
            if reservoir is None:
                report.missing_reservoirs.append(reservoir_name)
                continue

            for dataset in operation.datasets:
                self._safe_load(
                    lambda ds=dataset, r=reservoir: ds.load_reservoir_timeseries_from_dss(
                        dss_file_path=dss_file_path,
                        reservoir_dss_code=r.dss_location_code,
                        time_step=self.time_step,
                        fpart=fpart,
                    ),
                    dataset_name=dataset.name,
                    report=report,
                )

        # Zones
        for reservoir_name, zone_datasets in self._zones_copy.items():
            for zone_dataset in zone_datasets or []:
                if not zone_dataset:
                    continue
                self._safe_load(
                    lambda z=zone_dataset: z.load_timeseries_from_dss(self),
                    dataset_name=zone_dataset.name,
                    report=report,
                )

        if strict:
            report.raise_if_failed()
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_load(fn, *, dataset_name: str, report: "LoadReport") -> None:
        """Run a load closure, routing DSSLoadError into the report."""
        try:
            fn()
        except DSSPathNotFound as e:
            report.missing_paths.append((dataset_name, e.dss_path or ""))
        except DSSLoadError as e:
            report.read_errors.append((dataset_name, e.dss_path or "", str(e)))
        else:
            report.successes.append(dataset_name)

    @staticmethod
    def _suggest_similar_fparts(target: str, fparts: List[str], limit: int = 8) -> List[str]:
        """Return up to ``limit`` catalog F-parts most similar to ``target``.

        Uses difflib so we surface likely typo candidates (e.g. RIG_F03X vs
        RIG_F03E) without needing an exact prefix match.
        """
        import difflib
        return difflib.get_close_matches(target, fparts, n=limit, cutoff=0.5)
