from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import pandas as pd
from ressimplotter.dss_integration import (
    DSSReader,
    DSSLoadError,
    DSSFileNotFound,
    TimeSeriesContainer,
)

@dataclass
class Dataset:
    """Class for representing a geographical location."""

    name: str
    parameter: str
    path: Optional[Path] | str = None # will be loaded after simulation is created
    timeseries: Optional[TimeSeriesContainer] = None  # Populated by load_timeseries_from_dss()

    def __str__(self):
        # Handle path display
        if self.path:
            if isinstance(self.path, Path):
                path_display = str(self.path.name)  # Just filename for Path objects
            else:
                path_display = str(self.path)
        else:
            path_display = "None"
        
        # Handle timeseries display
        if self.timeseries is None:
            ts_info = "not loaded"
        else:
            try:
                length = len(self.timeseries.values) if self.timeseries.values is not None else 0
                start = getattr(self.timeseries, 'start_date', 'Unknown')
                units = getattr(self.timeseries, 'units', '')
                units_str = f", {units}" if units else ""
                ts_info = f"{length} records from {start}{units_str}"
            except Exception:
                ts_info = "loaded but error reading details"
        
        return f"Dataset({self.parameter} at {self.name}: {ts_info}, path={path_display})"
    
    def load_timeseries_from_dss(self, simulation) -> None:
        """Load time series data from DSS file using the simulation object.

        Raises:
            DSSFileNotFound: if the simulation's DSS file does not exist.
            DSSPathNotFound: if the DSS file does not contain the built path.
            DSSReadError: if the DSS library raises while reading.
        """
        dss_path = f"//{self.name}/{self.parameter}//{simulation.time_step}/{simulation.build_fpart()}/"
        dss_file_path = Path(simulation.dssFilePath)

        if not dss_file_path.exists():
            raise DSSFileNotFound(
                f"DSS file not found: {dss_file_path}",
                dss_file=dss_file_path,
                dss_path=dss_path,
                dataset_name=self.name,
            )

        dssreader = DSSReader(dss_file_path)
        try:
            tsc = dssreader.read_time_series(dss_path)
        except DSSLoadError as e:
            e.dataset_name = self.name
            self.path = dss_path
            raise

        self.timeseries = tsc
        self.path = dss_path

    def load_reservoir_timeseries_from_dss(self, dss_file_path: Path, reservoir_dss_code: str,
                                           time_step: str, fpart: str) -> None:
        """Load time series data from DSS file for this specific dataset.

        Args:
            dss_file_path: Path to the DSS file
            reservoir_dss_code: DSS B-part identifier for the reservoir
            time_step: Time step (e.g., "1HOUR")
            fpart: DSS F-part identifier (e.g., "C:000084|RID_F03A--0")

        Raises:
            DSSFileNotFound: if ``dss_file_path`` does not exist.
            DSSPathNotFound: if the DSS file does not contain the built path.
            DSSReadError: if the DSS library raises while reading.
        """
        dss_path = f"//{reservoir_dss_code}-POOL/{self.parameter}//{time_step}/{fpart}/"

        if not dss_file_path.exists():
            raise DSSFileNotFound(
                f"DSS file not found: {dss_file_path}",
                dss_file=dss_file_path,
                dss_path=dss_path,
                dataset_name=self.name,
            )

        dssreader = DSSReader(dss_file_path)
        try:
            tsc = dssreader.read_time_series(dss_path)
        except DSSLoadError as e:
            e.dataset_name = self.name
            self.path = dss_path
            raise

        self.timeseries = tsc
        self.path = dss_path
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the dataset's timeseries data to a pandas DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame with datetime index and values column,
                            or empty DataFrame if no timeseries data is loaded.
        
        Raises:
            ValueError: If timeseries data has not been loaded yet.
        """
        if self.timeseries is None:
            raise ValueError(f"No timeseries data loaded for dataset '{self.name}'. "
                           f"Call load_timeseries_from_dss() or load_reservoir_timeseries_from_dss() first.")
        
        # Use the TimeSeriesContainer's built-in to_dataframe method
        df = self.timeseries.to_dataframe()
        
        # Set datetime as index for time series analysis
        df = df.set_index('datetime')
        
        # Rename value column to be more descriptive
        df = df.rename(columns={'value': f'{self.parameter}'})
        
        # Add metadata as attributes
        df.attrs['name'] = self.name
        df.attrs['parameter'] = self.parameter
        df.attrs['path'] = self.path
        df.attrs['units'] = getattr(self.timeseries, 'units', 'Unknown')
        df.attrs['data_type'] = getattr(self.timeseries, 'data_type', 'Unknown')
        
        return df
    
    def to_dataframe_with_metadata(self) -> pd.DataFrame:
        """
        Convert to DataFrame with additional metadata columns.
        
        Returns:
            pandas.DataFrame: DataFrame with datetime, value, and metadata columns.
        """
        if self.timeseries is None:
            raise ValueError(f"No timeseries data loaded for dataset '{self.name}'. "
                           f"Call load_timeseries_from_dss() or load_reservoir_timeseries_from_dss() first.")
        
        # Get base DataFrame
        df = self.timeseries.to_dataframe()
        
        # Add metadata columns
        df['name'] = self.name
        df['parameter'] = self.parameter
        df['units'] = getattr(self.timeseries, 'units', 'Unknown')
        
        return df