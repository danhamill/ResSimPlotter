from dataclasses import dataclass
from typing import List
from ressimplotter.components.dataset import Dataset


@dataclass
class Operation:
    """
    Represents an operation type for a reservoir, including its time series data.
    """
    operation_type: str  # type of operation (standard, firo)
    description: str                    # Description of the operation
    datasets: List[Dataset]       # Time series data associated with this operation
    
    def __str__(self):
        dataset_names = [dataset.name for dataset in self.datasets]
        return f"Operation(type={self.operation_type}, description={self.description}, datasets=[{', '.join(dataset_names)}])"

    def get_time_series_by_name(self, name: str) -> Dataset:
        """
        Get a specific time series by name.
        
        Args:
            name: Name of the dataset to retrieve
            
        Returns:
            Dataset object
            
        Raises:
            ValueError: If dataset with the given name is not found
        """
        for ts in self.datasets:
            if ts.name == name:
                return ts
        
        # If we get here, the dataset wasn't found
        available_names = self.get_available_time_series_names()
        raise ValueError(f"Dataset '{name}' not found. Available datasets: {available_names}")
    
    def get_available_time_series_names(self) -> List[str]:
        """Get list of available time series names."""
        return [ts.name for ts in self.datasets]