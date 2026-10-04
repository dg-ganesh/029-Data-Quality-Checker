"""
Project : Data Quality Checker
Project ID : 029

Deequ Comparison Service
"""

from __future__ import annotations

from typing import Any


class DeequComparisonService:
    """Compare equivalent Python and Deequ validation results."""

    COMPARISON_MAP = {
        "CustomerID.required": {
            "python_rule": "REQ_001",
            "deequ_constraint": "CompletenessConstraint",
        },
        "Gender.required": {
            "python_rule": "REQ_002",
            "deequ_constraint": "CompletenessConstraint",
        },
        "MonthlyCharges.required": {
            "python_rule": "TYPE_001",
            "deequ_constraint": "CompletenessConstraint",
        },
        "MonthlyCharges.range": {
            "python_rule": "RANGE_001",
            "deequ_constraint": "MinimumConstraint",
        },
        "CustomerID.format": {
            "python_rule": "FORMAT_001",
            "deequ_constraint": "PatternMatchConstraint",
        },
    }

    def compare(
        self,
        python_results: list[dict[str, Any]],
        deequ_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Compare equivalent validation outcomes.

        Returns comparison records and an overall comparison status.
        """
        comparisons = []

        for comparison_name, mapping in self.COMPARISON_MAP.items():
            python_result = self._find_python_result(
                python_results,
                mapping["python_rule"],
            )

            deequ_result = self._find_deequ_result(
                deequ_results,
                mapping["deequ_constraint"],
            )

            python_status = self._normalize_python_status(
                python_result
            )

            deequ_status = self._normalize_deequ_status(
                deequ_result
            )

            comparisons.append(
                {
                    "comparison": comparison_name,
                    "python_rule": mapping["python_rule"],
                    "deequ_constraint": mapping["deequ_constraint"],
                    "python_status": python_status,
                    "deequ_status": deequ_status,
                    "match": self._statuses_match(
                        python_status,
                        deequ_status,
                    ),
                }
            )

        match_count = sum(
            1
            for item in comparisons
            if item["match"]
        )

        comparison_count = len(comparisons)

        overall_status = (
            "MATCH"
            if match_count == comparison_count
            else "DIFFERENCE"
        )

        return {
            "status": overall_status,
            "comparison_count": comparison_count,
            "match_count": match_count,
            "difference_count": (
                comparison_count - match_count
            ),
            "comparisons": comparisons,
        }

    @staticmethod
    def _find_python_result(
        results: list[dict[str, Any]],
        rule_id: str,
    ) -> dict[str, Any] | None:
        """Find a Python validation result by rule ID."""
        for result in results:
            if str(
                result.get("rule_id")
            ) == rule_id:
                return result

        return None

    @staticmethod
    def _find_deequ_result(
        results: list[dict[str, Any]],
        constraint_name: str,
    ) -> dict[str, Any] | None:
        """Find a Deequ result by constraint name."""
        for result in results:
            constraint = str(
                result.get("constraint")
                or result.get("constraint_name")
                or ""
            )

            if constraint_name in constraint:
                return result

        return None

    @staticmethod
    def _normalize_python_status(
        result: dict[str, Any] | None,
    ) -> str:
        """Normalize a Python validation result status."""
        if result is None:
            return "NOT_FOUND"

        status = str(
            result.get(
                "status",
                "UNKNOWN",
            )
        ).upper()

        if status == "PASS":
            return "PASS"

        if status in {"FAIL", "WARNING"}:
            return "FAIL"

        return status

    @staticmethod
    def _normalize_deequ_status(
        result: dict[str, Any] | None,
    ) -> str:
        """Normalize a Deequ validation result status."""
        if result is None:
            return "NOT_FOUND"

        status = str(
            result.get(
                "constraint_status",
                result.get(
                    "status",
                    "UNKNOWN",
                ),
            )
        ).upper()

        if status == "SUCCESS":
            return "PASS"

        if status == "FAILURE":
            return "FAIL"

        return status

    @staticmethod
    def _statuses_match(
        python_status: str,
        deequ_status: str,
    ) -> bool:
        """Return whether normalized statuses agree."""
        return (
            python_status == deequ_status
            and python_status != "NOT_FOUND"
        )


__all__ = ["DeequComparisonService"]