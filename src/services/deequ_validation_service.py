"""
Project : Data Quality Checker
Project ID : 029

Deequ Validation Service
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession

from src.core.deequ.deequ_validation_engine import (
    DeequValidationEngine,
)
from src.services.deequ_dataset_service import (
    DeequDatasetService,
)
from src.services.deequ_result_service import (
    DeequResultService,
)


class DeequValidationService:
    """Orchestrate dataset loading, Deequ validation, and persistence."""

    def __init__(
        self,
        spark: SparkSession,
        database_path: str | Path,
    ) -> None:
        """Initialize the Deequ validation service."""
        self.spark = spark

        self.dataset_service = DeequDatasetService(
            spark
        )

        self.validation_engine = DeequValidationEngine(
            spark
        )

        self.result_service = DeequResultService(
            database_path
        )

    def validate_file(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:
        """
        Load a CSV file, execute Deequ validation,
        and persist the validation results.
        """
        dataframe = self.dataset_service.load_csv(
            file_path
        )

        result = self.validation_engine.validate(
            dataframe
        )

        saved_count = self.result_service.save_results(
            result
        )

        return {
            "file_path": str(file_path),
            "status": result.get(
                "status",
                "UNKNOWN",
            ),
            "constraint_count": result.get(
                "constraint_count",
                0,
            ),
            "saved_count": saved_count,
            "constraints": result.get(
                "constraints",
                [],
            ),
        }


__all__ = ["DeequValidationService"]