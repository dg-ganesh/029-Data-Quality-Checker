"""
Project : Data Quality Checker
Project ID : 029

Deequ Profiling Service
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession

from src.core.deequ.deequ_profiling_engine import (
    DeequProfilingEngine,
)
from src.services.deequ_dataset_service import (
    DeequDatasetService,
)
from src.services.deequ_profiling_result_service import (
    DeequProfilingResultService,
)


class DeequProfilingService:
    """Orchestrate Deequ dataset profiling and result persistence."""

    def __init__(
        self,
        spark: SparkSession,
        database_path: str | Path,
    ) -> None:
        """Initialize the Deequ profiling service."""
        self.spark = spark

        self.dataset_service = DeequDatasetService(
            spark
        )

        self.profiling_engine = DeequProfilingEngine(
            spark
        )

        self.result_service = DeequProfilingResultService(
            database_path
        )

    def profile_file(
        self,
        file_path: str | Path,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Load a CSV file, execute Deequ profiling,
        and persist the profiling metrics.
        """
        dataframe = self.dataset_service.load_csv(
            file_path
        )

        result = self.profiling_engine.profile(
            dataframe,
            columns=columns,
        )

        saved_count = self.result_service.save_results(
            result
        )

        return {
            "file_path": str(file_path),
            "row_count": result.get(
                "row_count",
                0,
            ),
            "metric_count": len(
                result.get(
                    "metrics",
                    [],
                )
            ),
            "saved_count": saved_count,
            "metrics": result.get(
                "metrics",
                [],
            ),
        }


__all__ = ["DeequProfilingService"]
