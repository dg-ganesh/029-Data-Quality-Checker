"""
Project : Data Quality Checker
Project ID : 029

Quality Comparison Engine
"""

from src.models.quality_model import (
    ColumnQualityScore,
    QualityComparison,
    QualitySummary,
)


class QualityComparisonEngine:
    """Compares quality assessments between two dataset loads."""

    def compare(
        self,
        previous_summary: QualitySummary,
        current_summary: QualitySummary,
        previous_run_id: int,
        current_run_id: int,
        schema_changes: list[str] | None = None,
    ) -> QualityComparison:
        """Compare previous and current quality summaries."""
        previous_rules = self._build_rule_map(
            previous_summary
        )

        current_rules = self._build_rule_map(
            current_summary
        )

        new_failures = self._find_new_failures(
            previous_rules=previous_rules,
            current_rules=current_rules,
        )

        resolved_failures = self._find_resolved_failures(
            previous_rules=previous_rules,
            current_rules=current_rules,
        )

        previous_columns = self._build_column_map(
            previous_summary
        )

        current_columns = self._build_column_map(
            current_summary
        )

        improved_columns = self._find_column_changes(
            previous_columns=previous_columns,
            current_columns=current_columns,
            direction="improved",
        )

        deteriorated_columns = self._find_column_changes(
            previous_columns=previous_columns,
            current_columns=current_columns,
            direction="deteriorated",
        )

        return QualityComparison(
            current_run_id=current_run_id,
            previous_run_id=previous_run_id,
            current_score=current_summary.quality_score,
            previous_score=previous_summary.quality_score,
            score_change=round(
                current_summary.quality_score
                - previous_summary.quality_score,
                2,
            ),
            new_failures=new_failures,
            resolved_failures=resolved_failures,
            improved_columns=improved_columns,
            deteriorated_columns=deteriorated_columns,
            schema_changes=schema_changes or [],
        )

    @staticmethod
    def _build_rule_map(
        summary: QualitySummary,
    ) -> dict[str, object]:
        """Build a lookup of rule scores by rule ID."""
        rule_map: dict[str, object] = {}

        for column in summary.column_scores:
            for rule in column.rule_scores:
                rule_map[rule.rule_id] = rule

        return rule_map

    @staticmethod
    def _find_new_failures(
        previous_rules: dict,
        current_rules: dict,
    ) -> list[str]:
        """Find rules that now fail but previously did not."""
        failures: list[str] = []

        for rule_id, current_rule in current_rules.items():
            previous_rule = previous_rules.get(rule_id)

            if current_rule.status != "FAIL":
                continue

            if previous_rule is None:
                failures.append(rule_id)
                continue

            if previous_rule.status != "FAIL":
                failures.append(rule_id)

        return sorted(failures)

    @staticmethod
    def _find_resolved_failures(
        previous_rules: dict,
        current_rules: dict,
    ) -> list[str]:
        """Find rules that failed previously but now pass."""
        resolved: list[str] = []

        for rule_id, previous_rule in previous_rules.items():
            current_rule = current_rules.get(rule_id)

            if previous_rule.status != "FAIL":
                continue

            if current_rule is None:
                continue

            if current_rule.status != "FAIL":
                resolved.append(rule_id)

        return sorted(resolved)

    @staticmethod
    def _build_column_map(
        summary: QualitySummary,
    ) -> dict[str, ColumnQualityScore]:
        """Build a lookup of column scores by column name."""
        return {
            column.column_name: column
            for column in summary.column_scores
        }

    @staticmethod
    def _find_column_changes(
        previous_columns: dict[str, ColumnQualityScore],
        current_columns: dict[str, ColumnQualityScore],
        direction: str,
    ) -> list[str]:
        """Find columns whose quality moved in a given direction."""
        changed_columns: list[str] = []

        for column_name, current_column in current_columns.items():
            previous_column = previous_columns.get(
                column_name
            )

            if previous_column is None:
                continue

            score_change = (
                current_column.score
                - previous_column.score
            )

            if direction == "improved" and score_change > 0:
                changed_columns.append(column_name)

            elif (
                direction == "deteriorated"
                and score_change < 0
            ):
                changed_columns.append(column_name)

        return sorted(changed_columns)