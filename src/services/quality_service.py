"""
Project : Data Quality Checker
Project ID : 029

Quality Service
"""

from pathlib import Path

from src.core.quality.exception_classifier import ExceptionClassifier
from src.core.quality.quality_scoring_engine import QualityScoringEngine
from src.models.quality_model import QualitySummary
from src.models.validation_model import ValidationSummary
from src.services.quality_repository import QualityRepository


class QualityService:
    """Coordinates validation results and quality assessment."""

    def __init__(
        self,
        repository: QualityRepository | None = None,
        scoring_engine: QualityScoringEngine | None = None,
        exception_classifier: ExceptionClassifier | None = None,
    ):
        self.repository = repository or QualityRepository()

        self.scoring_engine = (
            scoring_engine or QualityScoringEngine()
        )

        self.exception_classifier = (
            exception_classifier or ExceptionClassifier()
        )

    def calculate_quality(
        self,
        validation_summary: ValidationSummary,
        dataset_name: str,
        file_path: str | Path,
        validation_run_id: int | None = None,
    ) -> tuple[QualitySummary, int]:
        """
        Calculate, classify, and persist a quality assessment.
        """

        quality_summary = (
            self.scoring_engine.calculate_quality(
                validation_summary
            )
        )

        quality_summary.dataset_name = dataset_name
        quality_summary.file_path = str(file_path)

        quality_summary.category_scores = (
            self.exception_classifier.classify_results(
                validation_summary.results
            )
        )

        quality_summary_id = (
            self.repository.save_quality_summary(
                summary=quality_summary,
                validation_run_id=validation_run_id,
            )
        )

        return (
            quality_summary,
            quality_summary_id,
        )

    def get_quality_history(
        self,
        dataset_name: str | None = None,
    ) -> list[dict]:
        """Return quality assessment history."""

        return self.repository.get_quality_history(
            dataset_name=dataset_name
        )

    def get_quality_summary_by_run(
        self,
        validation_run_id: int,
    ) -> dict | None:
        """Return the quality summary for a validation run."""

        return self.repository.get_quality_summary_by_run(
            validation_run_id=validation_run_id
        )

    def get_comparison_history(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """Return recent quality comparisons."""

        return self.repository.get_comparison_history(
            limit=limit
        )