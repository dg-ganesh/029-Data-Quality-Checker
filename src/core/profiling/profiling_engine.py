"""
Project : Data Quality Checker
Project ID : 029

Data Profiling Engine
"""

from datetime import datetime
from typing import Any

import pandas as pd

from src.models.dataset_model import ColumnProfile, DatasetProfile


class ProfilingEngine:
    """Generates dataset and column-level profiling information."""

    def profile_dataset(
        self,
        dataframe: pd.DataFrame,
        dataset_name: str,
        file_path: str,
    ) -> DatasetProfile:
        """
        Generate a complete profile for the supplied DataFrame.
        """
        row_count, column_count = dataframe.shape
        duplicate_row_count = int(dataframe.duplicated().sum())

        columns = [
            self._profile_column(dataframe, column_name)
            for column_name in dataframe.columns
        ]

        return DatasetProfile(
            dataset_name=dataset_name,
            file_path=file_path,
            row_count=int(row_count),
            column_count=int(column_count),
            duplicate_row_count=duplicate_row_count,
            profile_timestamp=datetime.now(),
            columns=columns,
        )

    def _profile_column(
        self,
        dataframe: pd.DataFrame,
        column_name: str,
    ) -> ColumnProfile:
        """Generate profiling information for one DataFrame column."""
        series = dataframe[column_name]

        total_count = len(series)
        null_count = int(series.isna().sum())
        non_null_count = total_count - null_count

        null_percentage = self._calculate_percentage(
            null_count,
            total_count,
        )

        unique_count = int(series.nunique(dropna=True))

        unique_percentage = self._calculate_percentage(
            unique_count,
            non_null_count,
        )

        profile = ColumnProfile(
            column_name=str(column_name),
            data_type=str(series.dtype),
            null_count=null_count,
            null_percentage=null_percentage,
            non_null_count=non_null_count,
            unique_count=unique_count,
            unique_percentage=unique_percentage,
        )

        if pd.api.types.is_numeric_dtype(series):
            self._populate_numeric_statistics(profile, series)

        else:
            self._populate_frequency_statistics(profile, series)

        return profile

    @staticmethod
    def _calculate_percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        """Calculate a percentage safely."""
        if denominator == 0:
            return 0.0

        return round((numerator / denominator) * 100, 2)

    @staticmethod
    def _populate_numeric_statistics(
        profile: ColumnProfile,
        series: pd.Series,
    ) -> None:
        """Populate statistical values for a numeric column."""
        numeric_series = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if numeric_series.empty:
            return

        profile.minimum = ProfilingEngine._normalize_value(
            numeric_series.min()
        )
        profile.maximum = ProfilingEngine._normalize_value(
            numeric_series.max()
        )
        profile.mean = ProfilingEngine._normalize_value(
            numeric_series.mean()
        )
        profile.median = ProfilingEngine._normalize_value(
            numeric_series.median()
        )
        profile.standard_deviation = ProfilingEngine._normalize_value(
            numeric_series.std()
        )

    @staticmethod
    def _populate_frequency_statistics(
        profile: ColumnProfile,
        series: pd.Series,
    ) -> None:
        """Populate most-frequent-value statistics."""
        non_null_series = series.dropna()

        if non_null_series.empty:
            return

        value_counts = non_null_series.value_counts()

        if value_counts.empty:
            return

        most_frequent_value = value_counts.index[0]
        most_frequent_count = int(value_counts.iloc[0])

        profile.most_frequent_value = ProfilingEngine._normalize_value(
            most_frequent_value
        )
        profile.most_frequent_count = most_frequent_count

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """
        Convert NumPy scalar values into native Python values
        where possible.
        """
        if hasattr(value, "item"):
            try:
                return value.item()
            except (ValueError, TypeError):
                pass

        return value