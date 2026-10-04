"""
Project : Data Quality Checker
Project ID : 029

Dataset Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DatasetInfo:
    """Represents metadata about an input dataset."""

    dataset_name: str
    file_path: str
    row_count: int
    column_count: int


@dataclass
class ColumnProfile:
    """Represents profiling information for a single dataset column."""

    column_name: str
    data_type: str
    null_count: int
    null_percentage: float
    non_null_count: int
    unique_count: int
    unique_percentage: float

    minimum: Any = None
    maximum: Any = None
    mean: Any = None
    median: Any = None
    standard_deviation: Any = None

    most_frequent_value: Any = None
    most_frequent_count: int = 0


@dataclass
class DatasetProfile:
    """Represents the complete profiling result for a dataset."""

    dataset_name: str
    file_path: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    profile_timestamp: datetime = field(default_factory=datetime.now)

    columns: list[ColumnProfile] = field(default_factory=list)