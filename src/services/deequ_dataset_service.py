"""
Project : Data Quality Checker
Project ID : 029

Deequ Dataset Service
"""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession


class DeequDatasetService:
    """Load Project 029 datasets into Spark DataFrames."""

    def __init__(self, spark: SparkSession) -> None:
        """Initialize the dataset service with a Spark session."""
        self.spark = spark

    def load_csv(
        self,
        file_path: str | Path,
    ) -> DataFrame:
        """
        Load a CSV dataset into a Spark DataFrame.

        The source file is read only and is never modified.
        """
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Dataset file not found: {path}"
            )

        return (
            self.spark.read
            .option("header", "true")
            .option("inferSchema", "true")
            .csv(str(path))
        )

    @staticmethod
    def get_metadata(dataframe: DataFrame) -> dict[str, object]:
        """Return basic metadata for a Spark DataFrame."""
        return {
            "row_count": dataframe.count(),
            "column_count": len(dataframe.columns),
            "columns": dataframe.columns,
        }


__all__ = ["DeequDatasetService"]