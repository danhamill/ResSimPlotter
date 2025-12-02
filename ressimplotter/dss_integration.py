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
            raise FileNotFoundError(f"DSS file not found: {self.file_path}")
    
    def get_catalog(self) -> List[str]:
        """Get catalog of all paths in the DSS file."""
        try:
            with HecDss(str(self.file_path)) as dss:
                catalog = dss.get_catalog()
                return catalog.rawCatalog if hasattr(catalog, 'rawCatalog') else []
        except Exception as e:
            logging.error(f"Error reading DSS catalog: {e}")
            return []
    
    def read_time_series(self, dss_path: Union[str, DssPath]) -> Optional[TimeSeriesContainer]:
        """
        Read time series data from DSS file.
        
        Args:
            dss_path: DSS path as string or DssPath object
            
        Returns:
            DSSTimeSeriesData object or None if not found
        """
        path_str = dss_path.to_string() if isinstance(dss_path, DssPath) else dss_path
        
        try:
            with HecDss(str(self.file_path)) as dss:
                # Get the time series data
                ts_data = dss.get(path_str)
                
                if ts_data is None:
                    logging.warning(f"No data found for path: {path_str}")
                    return None
                
                # Convert to our format
                return TimeSeriesContainer(
                    path=path_str,
                    start_date=ts_data.start_date,
                    times=ts_data.times,
                    values=ts_data.values,
                    units=getattr(ts_data, 'units', ''),
                    data_type=getattr(ts_data, 'data_type', ''),
                    interval=getattr(ts_data, 'interval', '')
                )
                
        except Exception as e:
            logging.error(f"Error reading time series from {path_str}: {e}")
            return None
    
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


# class SystemDSSProcessor:
#     """
#     High-level processor that combines the system architecture with DSS operations.
#     Provides methods to extract data for specific reservoirs, operations, and time series.
#     """
    
#     def __init__(self, system: Optional[System] = None):
#         """
#         Initialize with a system configuration.
        
#         Args:
#             system: System configuration (defaults to standard system)
#         """
#         self.system = system or create_default_system()
    
#     def process_reservoir_data(self, dss_reader: DSSReader, 
#                              reservoir_name: str, operation_name: str,
#                              study_pattern: str = "*",
#                              start_date_pattern: str = "*",
#                              interval_pattern: str = "*",
#                              version_pattern: str = "*") -> Dict[str, TimeSeriesContainer]:
#         """
#         Extract all time series data for a specific reservoir and operation.
        
#         Args:
#             dss_reader: DSS file reader
#             reservoir_name: Name of reservoir (e.g., "ORO", "NBB")
#             operation_name: Name of operation (e.g., "Normal", "FIRO") 
#             study_pattern: Study name pattern (A-part)
#             start_date_pattern: Start date pattern (D-part)
#             interval_pattern: Interval pattern (E-part)
#             version_pattern: Version pattern (F-part)
            
#         Returns:
#             Dictionary mapping time series names to data
#         """
#         results = {}
        
#         # Get reservoir and operation from system
#         reservoir = self.system.get_reservoir_by_name(reservoir_name)
#         if not reservoir:
#             logging.error(f"Reservoir '{reservoir_name}' not found")
#             return results
            
#         operation = reservoir.get_operation_by_name(operation_name)
#         if not operation:
#             logging.error(f"Operation '{operation_name}' not found for reservoir '{reservoir_name}'")
#             return results
        
#         # Build DSS paths for each time series in the operation
#         for time_series in operation.time_series:
#             dss_path = DSSPath(
#                 study=study_pattern,
#                 location=reservoir.dss_location_code,
#                 parameter=time_series.dss_parameter,
#                 start_date=start_date_pattern,
#                 interval=interval_pattern,
#                 version=version_pattern
#             )
            
#             # Find matching paths in the DSS file
#             pattern = dss_path.to_string()
#             matching_paths = dss_reader.find_paths_by_pattern(pattern)
            
#             if matching_paths:
#                 # Use the first matching path (could be enhanced to handle multiple matches)
#                 path = matching_paths[0]
#                 logging.info(f"Reading {time_series.name} from {path}")
                
#                 data = dss_reader.read_time_series(path)
#                 if data:
#                     results[time_series.name] = data
#                 else:
#                     logging.warning(f"No data retrieved for {time_series.name} at {path}")
#             else:
#                 logging.warning(f"No paths found matching pattern: {pattern}")
        
#         return results
    
#     def export_to_feather(self, reservoir_data: Dict[str, TimeSeriesContainer], 
#                          output_path: Union[str, Path],
#                          reservoir_name: str) -> bool:
#         """
#         Export reservoir data to feather format compatible with existing workflows.
        
#         Args:
#             reservoir_data: Dictionary of time series data
#             output_path: Path for output feather file
#             reservoir_name: Name of reservoir for metadata
            
#         Returns:
#             True if successful, False otherwise
#         """
#         try:
#             # Combine all time series into a single DataFrame
#             combined_data = []
            
#             for ts_name, ts_data in reservoir_data.items():
#                 df = ts_data.to_feather_format()
#                 df['reservoir'] = reservoir_name
#                 df['time_series'] = ts_name
#                 combined_data.append(df)
            
#             if combined_data:
#                 # Concatenate all DataFrames
#                 final_df = pd.concat(combined_data, ignore_index=True)
                
#                 # Save to feather format
#                 final_df.to_feather(output_path)
#                 logging.info(f"Successfully exported to {output_path}")
#                 return True
#             else:
#                 logging.warning("No data to export")
#                 return False
                
#         except Exception as e:
#             logging.error(f"Error exporting to feather: {e}")
#             return False
    
#     def process_pattern_scenario(self, dss_file_path: Union[str, Path],
#                                pattern_year: str, scale_factor: int,
#                                arc_spillway_config: str, dataset: str,
#                                operation_name: str = "Normal") -> Dict[str, str]:
#         """
#         Process a complete pattern scenario (all reservoirs) and export feather files.
        
#         Args:
#             dss_file_path: Path to DSS file
#             pattern_year: Year pattern
#             scale_factor: Scale factor
#             arc_spillway_config: Arc spillway configuration
#             dataset: Dataset name
#             operation_name: Operation name
            
#         Returns:
#             Dictionary mapping reservoir names to output file paths
#         """
#         results = {}
        
#         try:
#             dss_reader = DSSReader(dss_file_path)
            
#             # Process each reservoir
#             for reservoir in self.system.reservoirs:
#                 logging.info(f"Processing reservoir: {reservoir.name}")
                
#                 # Extract data for this reservoir
#                 reservoir_data = self.process_reservoir_data(
#                     dss_reader=dss_reader,
#                     reservoir_name=reservoir.name,
#                     operation_name=operation_name,
#                     study_pattern=f"PATTERN_{pattern_year}_SF_{scale_factor}_{dataset}"
#                 )
                
#                 if reservoir_data:
#                     # Build output file path
#                     operation = reservoir.get_operation_by_name(operation_name)
#                     suffix = operation.suffix if operation else ""
                    
#                     output_file = f"data/{pattern_year}_{scale_factor}_{arc_spillway_config}_{dataset}_Alt3{suffix}.feather"
                    
#                     # Export to feather
#                     if self.export_to_feather(reservoir_data, output_file, reservoir.name):
#                         results[reservoir.name] = output_file
                        
#         except Exception as e:
#             logging.error(f"Error processing pattern scenario: {e}")
        
#         return results


# Factory functions
def create_dss_reader(dss_file_path: Union[str, Path]) -> Optional[DSSReader]:
    """Create a DSS reader with error handling."""
    try:
        return DSSReader(dss_file_path)
    except Exception as e:
        logging.error(f"Failed to create DSS reader: {e}")
        return None


# def create_system_processor(system: Optional[System] = None) -> SystemDSSProcessor:
#     """Create a system DSS processor."""
#     return SystemDSSProcessor(system)


# Utility functions
def validate_dss_installation() -> bool:
    """Check if HEC-DSS Python is properly installed."""
    return HEC_DSS_AVAILABLE


def get_dss_file_info(dss_file_path: Union[str, Path]) -> Dict[str, any]:
    """Get basic information about a DSS file."""
    info = {
        'file_exists': False,
        'file_size': 0,
        'record_count': 0,
        'sample_paths': []
    }
    
    file_path = Path(dss_file_path)
    info['file_exists'] = file_path.exists()
    
    if info['file_exists']:
        info['file_size'] = file_path.stat().st_size
        
        try:
            reader = DSSReader(file_path)
            catalog = reader.get_catalog()
            info['record_count'] = len(catalog)
            info['sample_paths'] = catalog[:10]  # First 10 paths as sample
        except Exception as e:
            logging.warning(f"Could not read DSS file details: {e}")
    
    return info