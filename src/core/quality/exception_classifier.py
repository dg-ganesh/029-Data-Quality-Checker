"""
Project : Data Quality Checker
Project ID : 029

Data Quality Exception Classifier
"""

from collections import defaultdict

from src.models.quality_model import (
    QualityCategoryScore,
    RuleQualityScore,
)
from src.models.validation_model import (
    ValidationResult,
)


CATEGORY_NAMES = {
    "required": "Missing Data",
    "blank": "Blank Data",
    "unique": "Duplicates",
    "duplicate": "Duplicates",
    "datatype": "Datatype",
    "range": "Range",
    "format": "Format",
    "business_rule": "Business Rule",
}


class ExceptionClassifier:
    """Classifies validation results into quality categories."""

    def classify_results(
        self,
        results: list[ValidationResult],
    ) -> list[QualityCategoryScore]:
        """Classify validation results by quality category."""
        grouped_results = self._group_results_by_category(
            results
        )

        category_scores: list[
            QualityCategoryScore
        ] = []

        for category_name, category_results in (
            grouped_results.items()
        ):
            category_scores.append(
                self._build_category_score(
                    category_name=category_name,
                    results=category_results,
                )
            )

        return category_scores

    @staticmethod
    def get_category_name(
        rule_type: str,
    ) -> str:
        """Return the quality category for a rule type."""
        return CATEGORY_NAMES.get(
            rule_type,
            "Other",
        )

    def _group_results_by_category(
        self,
        results: list[ValidationResult],
    ) -> dict[str, list[ValidationResult]]:
        """Group validation results by quality category."""
        grouped_results: dict[
            str,
            list[ValidationResult],
        ] = defaultdict(list)

        for result in results:
            category_name = self.get_category_name(
                result.rule_type
            )

            grouped_results[category_name].append(
                result
            )

        return dict(grouped_results)

    @staticmethod
    def _build_category_score(
        category_name: str,
        results: list[ValidationResult],
    ) -> QualityCategoryScore:
        """Build a category-level quality summary."""
        total_rules = len(results)

        failed_rules = sum(
            1
            for result in results
            if result.status == "FAIL"
        )

        total_failed_records = sum(
            result.failed_records
            for result in results
        )

        score = _calculate_category_score(
            results
        )

        return QualityCategoryScore(
            category_name=category_name,
            total_rules=total_rules,
            failed_rules=failed_rules,
            total_failed_records=total_failed_records,
            score=score,
        )

    @staticmethod
    def classify_rule_score(
        rule_score: RuleQualityScore,
    ) -> str:
        """Classify a scored rule into a quality category."""
        return ExceptionClassifier.get_category_name(
            rule_score.rule_type
        )


def _calculate_category_score(
    results: list[ValidationResult],
) -> float:
    """Calculate the average quality score for a category."""
    if not results:
        return 100.0

    scores: list[float] = []

    for result in results:
        failure_percentage = min(
            max(result.failure_percentage, 0.0),
            100.0,
        )

        scores.append(
            100.0 - failure_percentage
        )

    return round(
        sum(scores) / len(scores),
        2,
    )