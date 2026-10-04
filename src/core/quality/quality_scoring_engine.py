"""
Project : Data Quality Checker
Project ID : 029

Quality Scoring Engine
"""

from collections import defaultdict

from src.models.quality_model import (
    ColumnQualityScore,
    QualityCategoryScore,
    QualitySummary,
    RuleQualityScore,
)
from src.models.validation_model import (
    ValidationResult,
    ValidationSummary,
)


class QualityScoringEngine:
    """Calculates dataset quality scores from validation results."""

    def calculate_quality(
        self,
        validation_summary: ValidationSummary,
    ) -> QualitySummary:
        """Calculate the complete quality assessment."""
        rule_scores = [
            self._calculate_rule_score(result)
            for result in validation_summary.results
        ]

        column_scores = self._calculate_column_scores(
            rule_scores
        )

        category_scores = self._calculate_category_scores(
            rule_scores
        )

        overall_score = self._calculate_overall_score(
            rule_scores
        )

        return QualitySummary(
            dataset_name=validation_summary.dataset_name,
            file_path=validation_summary.file_path,
            quality_score=overall_score,
            total_rules=validation_summary.total_rules,
            passed_rules=validation_summary.passed_rules,
            failed_rules=validation_summary.failed_rules,
            warning_rules=validation_summary.warning_rules,
            total_failed_records=(
                validation_summary.total_failed_records
            ),
            column_scores=column_scores,
            category_scores=category_scores,
        )

    @staticmethod
    def _calculate_rule_score(
        result: ValidationResult,
    ) -> RuleQualityScore:
        """Calculate the 0-100 score for one validation rule."""
        failure_percentage = min(
            max(result.failure_percentage, 0.0),
            100.0,
        )

        score = round(
            100.0 - failure_percentage,
            2,
        )

        return RuleQualityScore(
            rule_id=result.rule_id,
            column_name=result.column_name,
            rule_type=result.rule_type,
            status=result.status,
            total_records=result.total_records,
            failed_records=result.failed_records,
            failure_percentage=failure_percentage,
            score=score,
            severity=_get_severity(result),
            message=result.message,
        )

    @staticmethod
    def _calculate_column_scores(
        rule_scores: list[RuleQualityScore],
    ) -> list[ColumnQualityScore]:
        """Aggregate rule scores by column."""
        grouped_rules: dict[
            str,
            list[RuleQualityScore],
        ] = defaultdict(list)

        for rule_score in rule_scores:
            grouped_rules[
                rule_score.column_name
            ].append(rule_score)

        column_scores: list[ColumnQualityScore] = []

        for column_name, rules in grouped_rules.items():
            total_rules = len(rules)

            passed_rules = sum(
                1
                for rule in rules
                if rule.status == "PASS"
            )

            failed_rules = sum(
                1
                for rule in rules
                if rule.status == "FAIL"
            )

            warning_rules = sum(
                1
                for rule in rules
                if rule.status == "WARNING"
            )

            total_failed_records = sum(
                rule.failed_records
                for rule in rules
            )

            score = _average(
                rule.score
                for rule in rules
            )

            column_scores.append(
                ColumnQualityScore(
                    column_name=column_name,
                    total_rules=total_rules,
                    passed_rules=passed_rules,
                    failed_rules=failed_rules,
                    warning_rules=warning_rules,
                    total_failed_records=(
                        total_failed_records
                    ),
                    score=score,
                    rule_scores=rules,
                )
            )

        return column_scores

    @staticmethod
    def _calculate_category_scores(
        rule_scores: list[RuleQualityScore],
    ) -> list[QualityCategoryScore]:
        """Aggregate rule scores by validation category."""
        grouped_rules: dict[
            str,
            list[RuleQualityScore],
        ] = defaultdict(list)

        for rule_score in rule_scores:
            category = _get_category(
                rule_score.rule_type
            )

            grouped_rules[category].append(
                rule_score
            )

        category_scores: list[
            QualityCategoryScore
        ] = []

        for category_name, rules in grouped_rules.items():
            total_rules = len(rules)

            failed_rules = sum(
                1
                for rule in rules
                if rule.status == "FAIL"
            )

            total_failed_records = sum(
                rule.failed_records
                for rule in rules
            )

            score = _average(
                rule.score
                for rule in rules
            )

            category_scores.append(
                QualityCategoryScore(
                    category_name=category_name,
                    total_rules=total_rules,
                    failed_rules=failed_rules,
                    total_failed_records=(
                        total_failed_records
                    ),
                    score=score,
                )
            )

        return category_scores

    @staticmethod
    def _calculate_overall_score(
        rule_scores: list[RuleQualityScore],
    ) -> float:
        """Calculate the overall dataset quality score."""
        if not rule_scores:
            return 100.0

        return _average(
            rule.score
            for rule in rule_scores
        )


def _average(values) -> float:
    """Return the rounded arithmetic average."""
    values_list = list(values)

    if not values_list:
        return 0.0

    return round(
        sum(values_list) / len(values_list),
        2,
    )


def _get_category(rule_type: str) -> str:
    """Map a validation rule type to a quality category."""
    categories = {
        "required": "Missing Data",
        "blank": "Blank Data",
        "unique": "Duplicates",
        "duplicate": "Duplicates",
        "datatype": "Datatype",
        "range": "Range",
        "format": "Format",
        "business_rule": "Business Rule",
    }

    return categories.get(
        rule_type,
        "Other",
    )


def _get_severity(result: ValidationResult) -> str:
    """Derive severity from the validation status."""
    if result.status in {"FAIL", "WARNING"}:
        return result.status

    return "PASS"