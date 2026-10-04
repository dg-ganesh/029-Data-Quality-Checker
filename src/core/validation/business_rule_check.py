"""
Project : Data Quality Checker
Project ID : 029

Business-Rule Validation
"""

from typing import Any, Callable

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


SUPPORTED_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "equals": lambda actual, expected: actual == expected,
    "not_equals": lambda actual, expected: actual != expected,
    "greater_than": lambda actual, expected: actual > expected,
    "greater_than_or_equal": lambda actual, expected: actual >= expected,
    "less_than": lambda actual, expected: actual < expected,
    "less_than_or_equal": lambda actual, expected: actual <= expected,
}


def validate_business_rule(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate records against a configurable business rule.

    Required parameters:
        operator
        expected_value

    The rule operates against rule.column_name.
    """
    column_name = rule.column_name

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Business-rule check column '{column_name}' "
                "does not exist in the dataset."
            ),
        )

    operator_name = str(
        rule.parameters.get("operator", "")
    ).lower().strip()

    if operator_name not in SUPPORTED_OPERATORS:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Unsupported business-rule operator "
                f"'{operator_name}'."
            ),
        )

    if "expected_value" not in rule.parameters:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                "Business-rule configuration requires "
                "'expected_value'."
            ),
        )

    expected_value = rule.parameters["expected_value"]
    operator = SUPPORTED_OPERATORS[operator_name]

    failed_records = _build_failed_records(
        series=dataframe[column_name],
        operator=operator,
        operator_name=operator_name,
        expected_value=expected_value,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(dataframe),
        failed_records=failed_records,
        message=_build_result_message(
            column_name=column_name,
            operator_name=operator_name,
            expected_value=expected_value,
            failed_count=len(failed_records),
        ),
    )


def _build_failed_records(
    series: pd.Series,
    operator: Callable[[Any, Any], bool],
    operator_name: str,
    expected_value: Any,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for business-rule violations."""
    failed_records: list[FailedRecord] = []

    for index, actual_value in series.items():
        if pd.isna(actual_value):
            continue

        try:
            is_valid = operator(
                actual_value,
                expected_value,
            )
        except (TypeError, ValueError):
            is_valid = False

        if not is_valid:
            failed_records.append(
                FailedRecord(
                    row_number=int(index) + 1,
                    column_name=rule.column_name,
                    rule_id=rule.rule_id,
                    actual_value=actual_value,
                    expected_value=(
                        f"{operator_name} {expected_value}"
                    ),
                    message=(
                        f"Business rule violated for "
                        f"'{rule.column_name}': "
                        f"value {actual_value!r} does not "
                        f"satisfy {operator_name} "
                        f"{expected_value!r}."
                    ),
                )
            )

    return failed_records


def _build_result_message(
    column_name: str,
    operator_name: str,
    expected_value: Any,
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    rule_description = (
        f"{column_name} {operator_name} {expected_value!r}"
    )

    if failed_count == 0:
        return (
            f"Business-rule check passed: "
            f"{rule_description}."
        )

    return (
        f"Business-rule check found {failed_count} "
        f"violation(s): {rule_description}."
    )