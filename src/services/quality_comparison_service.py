"""
Project : Data Quality Checker
Project ID : 029

Historical Quality Comparison Service
"""

import pandas as pd

from src.core.quality.quality_comparison_engine import (
    QualityComparisonEngine,
)
from src.core.quality.schema_comparison_engine import (
    SchemaComparisonEngine,
)
from src.models.quality_model import QualityComparison, QualitySummary
from src.services.load_history_service import LoadHistoryService
from src.services.quality_repository import QualityRepository


class QualityComparisonService:
    """Coordinates historical quality and schema comparisons."""

    def __init__(
        self,
        history_service: LoadHistoryService | None = None,
        repository: QualityRepository | None = None,
        comparison_engine: QualityComparisonEngine | None = None,
        schema_engine: SchemaComparisonEngine | None = None,
    ):
        self.history_service = (
            history_service or LoadHistoryService()
        )

        self.repository = (
            repository or QualityRepository()
        )

        self.comparison_engine = (
            comparison_engine or QualityComparisonEngine()
        )

        self.schema_engine = (
            schema_engine or SchemaComparisonEngine()
        )

    def compare_quality(
        self,
        current_summary: QualitySummary,
        current_run_id: int,
        current_dataframe: pd.DataFrame,
        previous_summary: QualitySummary | None = None,
        previous_run_id: int | None = None,
        previous_dataframe: pd.DataFrame | None = None,
    ) -> QualityComparison | None:
        """
        Compare the current quality assessment with the
        previous quality assessment.
        """

        if (
            previous_summary is None
            or previous_run_id is None
        ):
            return None

        schema_changes: list[str] = []

        if previous_dataframe is not None:
            schema_comparison = (
                self.schema_engine.compare(
                    previous_dataframe=previous_dataframe,
                    current_dataframe=current_dataframe,
                )
            )

            schema_changes = [
                change.message
                for change in schema_comparison.get_all_changes()
            ]

        comparison = self.comparison_engine.compare(
            previous_summary=previous_summary,
            current_summary=current_summary,
            previous_run_id=previous_run_id,
            current_run_id=current_run_id,
            schema_changes=schema_changes,
        )

        self.repository.save_comparison(
            comparison
        )

        return comparison

    def get_previous_quality_summary(
        self,
        dataset_name: str,
        current_run_id: int,
    ) -> tuple[int, QualitySummary] | None:
        """
        Retrieve the complete quality summary belonging
        to the previous validation run.
        """

        history = (
            self.history_service.get_load_history(
                dataset_name=dataset_name
            )
        )

        previous_run_id = self._find_previous_run_id(
            history=history,
            current_run_id=current_run_id,
        )

        if previous_run_id is None:
            return None

        previous_summary = (
            self.repository.get_quality_summary_by_run(
                validation_run_id=previous_run_id
            )
        )

        if previous_summary is None:
            return None

        return (
            previous_run_id,
            previous_summary,
        )

    @staticmethod
    def _find_previous_run_id(
        history: list,
        current_run_id: int,
    ) -> int | None:
        """Find the most recent run before the current run."""

        previous_run_id = None

        for record in history:
            if record.run_id < current_run_id:
                previous_run_id = record.run_id
                break

        return previous_run_id

    def get_comparison_history(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """Return historical quality comparisons."""

        return self.repository.get_comparison_history(
            limit=limit
        )