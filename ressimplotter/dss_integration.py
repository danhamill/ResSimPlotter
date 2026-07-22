"""
DSS Integration module for the Robustness Viewer using HEC-DSS Python.

This module provides DSS file operations using the official HEC-DSS Python library
and integrates with our object-oriented system architecture.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging
from hecdss.dsspath import DssPath

try:
    from hecdss import HecDss
    HEC_DSS_AVAILABLE = True
except ImportError:
    HEC_DSS_AVAILABLE = False
    logging.warning("HEC-DSS Python library not available. Install with: pip install hecdss")


class DSSLoadError(Exception):
    """Base class for DSS load failures. Carries structured context so the
    caller can distinguish "file missing" vs "path not in file" vs "read error"
    and can build informative error messages."""

    def __init__(
        self,
        message: str,
        *,
        dss_file: Optional[Union[str, Path]] = None,
        dss_path: Optional[str] = None,
        dataset_name: Optional[str] = None,
        simulation_id: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.dss_file = str(dss_file) if dss_file is not None else None
        self.dss_path = dss_path
        self.dataset_name = dataset_name
        self.simulation_id = simulation_id
        self.cause = cause


class DSSFileNotFound(DSSLoadError):
    """The DSS file itself does not exist on disk."""


class DSSPathNotFound(DSSLoadError):
    """The DSS file was opened, but the requested path is not present."""


class DSSReadError(DSSLoadError):
    """The DSS file and path exist, but reading raised an unexpected error."""


@dataclass
class TimeSeriesContainer:
    """
    Container for time series data retrieved from DSS files.
    Maps to HEC-DSS Python TimeSeries objects.
    """
    path: str                          # DSS path
    start_date: datetime               # Start date
    times: List[datetime]              # Time stamps  
    values: List[float]                # Data values
    units: str                         # Data units
    data_type: str                     # DSS data type (PER-AVER, INST-VAL, etc.)
    interval: str                      # Time interval
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame({
            'datetime': self.times,
            'value': self.values
        })
    
    def to_feather_format(self) -> pd.DataFrame:
        """Convert to format compatible with existing feather workflows."""
        df = pd.DataFrame({
            'datetime': self.times,
            'value': self.values
        })
        # Add any additional columns expected by the feather format
        df['units'] = self.units
        df['path'] = self.path
        return df
    
    def __str__(self):
        try:
            num_points = len(self.values) if self.values is not None else 0
            start_str = self.start_date.strftime('%Y-%m-%d %H:%M') if self.start_date else 'Unknown'
            return f"TimeSeries(path={self.path}, start={start_str}, points={num_points}, units={self.units})"
        except Exception as e:
            return f"TimeSeries(path={self.path}, error accessing data: {str(e)})"
    
    def __repr__(self):
        return self.__str__()


class DSSReader:
    """
    DSS file reader using HEC-DSS Python library.
    Provides high-level interface for reading time series data.
    """
    
    def __init__(self, dss_file_path: Union[str, Path]):
        """
        Initialize DSS reader.
        
        Args:
            dss_file_path: Path to DSS file
        """
        self.file_path = Path(dss_file_path)
        
        if not HEC_DSS_AVAILABLE:
            raise ImportError("HEC-DSS Python library not available. Install with: pip install hecdss")

        if not self.file_path.exists():
            raise DSSFileNotFound(
                f"DSS file not found: {self.file_path}",
                dss_file=self.file_path,
            )
    
    def get_catalog(self) -> List[str]:
        """Get catalog of all paths in the DSS file.

        Returns the uncondensed path list (one path per record). Falls back to
        legacy attribute names for older ``hecdss`` versions.
        """
        try:
            with HecDss(str(self.file_path)) as dss:
                catalog = dss.get_catalog()
                for attr in ("uncondensed_paths", "rawCatalog"):
                    paths = getattr(catalog, attr, None)
                    if paths:
                        return list(paths)
                return []
        except Exception as e:
            logging.error(f"Error reading DSS catalog: {e}")
            return []
    
    def read_time_series(self, dss_path: Union[str, DssPath]) -> TimeSeriesContainer:
        """
        Read time series data from DSS file.

        Args:
            dss_path: DSS path as string or DssPath object

        Returns:
            TimeSeriesContainer for the requested path.

        Raises:
            DSSPathNotFound: if the DSS file does not contain the requested path.
            DSSReadError: if the DSS library raises while reading.
        """
        path_str = dss_path.to_string() if isinstance(dss_path, DssPath) else dss_path

        try:
            with HecDss(str(self.file_path)) as dss:
                ts_data = dss.get(path_str)
        except KeyError as e:
            # hecdss raises KeyError when the requested path is not in the file.
            raise DSSPathNotFound(
                f"No data found for path: {path_str}",
                dss_file=self.file_path,
                dss_path=path_str,
                cause=e,
            ) from e
        except Exception as e:
            raise DSSReadError(
                f"Error reading time series from {path_str}: {e}",
                dss_file=self.file_path,
                dss_path=path_str,
                cause=e,
            ) from e

        if ts_data is None:
            raise DSSPathNotFound(
                f"No data found for path: {path_str}",
                dss_file=self.file_path,
                dss_path=path_str,
            )

        return TimeSeriesContainer(
            path=path_str,
            start_date=ts_data.start_date,
            times=ts_data.times,
            values=ts_data.values,
            units=getattr(ts_data, 'units', ''),
            data_type=getattr(ts_data, 'data_type', ''),
            interval=getattr(ts_data, 'interval', ''),
        )

    def has_path(self, dss_path: str) -> bool:
        """Return True if ``dss_path`` is present in the DSS catalog."""
        return dss_path in self.get_catalog()

    def get_fparts(self) -> List[str]:
        """Return the sorted, unique set of F-parts present in the catalog."""
        fparts = set()
        for raw in self.get_catalog():
            parts = raw.split('/')
            # A well-formed DSS path is "/A/B/C/D/E/F/" -> 8 tokens with empty ends;
            # F is the second-to-last token.
            if len(parts) >= 7:
                fparts.add(parts[-2])
        return sorted(fparts)
    
    def find_paths_by_pattern(self, pattern: str) -> List[str]:
        """
        Find DSS paths matching a pattern (with wildcards).
        
        Args:
            pattern: DSS path pattern (e.g., "/STUDY/*/FLOW/*/*/*/")
            
        Returns:
            List of matching paths
        """
        catalog = self.get_catalog()
        matching_paths = []
        
        # Convert DSS wildcard pattern to regex
        regex_pattern = pattern.replace('*', '[^/]*')
        regex_pattern = regex_pattern.replace('?', '[^/]')
        
        import re
        compiled_pattern = re.compile(regex_pattern)
        
        for path in catalog:
            if compiled_pattern.match(path):
                matching_paths.append(path)
        
        return matching_paths
    
    def read_multiple_time_series(self, paths: List[str]) -> Dict[str, TimeSeriesContainer]:
        """
        Read multiple time series efficiently.
        
        Args:
            paths: List of DSS paths to read
            
        Returns:
            Dictionary mapping paths to DSSTimeSeriesData objects
        """
        results = {}
        
        try:
            with HecDss(str(self.file_path)) as dss:
                for path in paths:
                    try:
                        ts_data = dss.get(path)
                        if ts_data is not None:
                            results[path] = TimeSeriesContainer(
                                path=path,
                                start_date=ts_data.start_date,
                                times=ts_data.times,
                                values=ts_data.values,
                                units=getattr(ts_data, 'units', ''),
                                data_type=getattr(ts_data, 'data_type', ''),
                                interval=getattr(ts_data, 'interval', '')
                            )
                    except Exception as e:
                        logging.warning(f"Failed to read {path}: {e}")
                        
        except Exception as e:
            logging.error(f"Error in batch read: {e}")
        
        return results
