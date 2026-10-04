"""
Project : Data Quality Checker
Project ID : 029

Range Validation
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


def validate_range(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate that values fall within the configured range.

    The rule may specify:
        minimum
        maximum

    Either boundary may be omitted.
    """
    column_name = rule.column_name

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Range check column '{column_name}' "
                "does not exist in the dataset."
            ),
        )

    parameters = rule.parameters

    minimum = parameters.get("minimum")
    maximum = parameters.get("maximum")

    if minimum is None and maximum is None:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Range check for '{column_name}' requires "
                "at least a minimum or maximum value."
            ),
        )

    series = dataframe[column_name]

    failed_records = _build_failed_records(
        series=series,
        minimum=minimum,
        maximum=maximum,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(series),
        failed_records=failed_records,
        message=_build_result_message(
            column_name=column_name,
            minimum=minimum,
            maximum=maximum,
            failed_count=len(failed_records),
        ),
    )


def _build_failed_records(
    series: pd.Series,
    minimum: Any,
    maximum: Any,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for out-of-range values."""
    failed_records: list[FailedRecord] = []

    for index, value in series.items():
        if pd.isna(value):
            continue

        if not _is_comparable_value(
            value=value,
            minimum=minimum,
            maximum=maximum,
        ):
            failed_records.append(
                _build_failed_record(
                    index=index,
                    value=value,
                    minimum=minimum,
                    maximum=maximum,
                    rule=rule,
                    message="Value cannot be evaluated against the configured range.",
                )
            )
            continue

        if minimum is not None and value < minimum:
            failed_records.append(
                _build_failed_record(
                    index=index,
                    value=value,
                    minimum=minimum,
                    maximum=maximum,
                    rule=rule,
                    message=f"Value is below the minimum of {minimum}.",
                )
            )
            continue

        if maximum is not None and value > maximum:
            failed_records.append(
                _build_failed_record(
                    index=index,
                    value=value,
                    minimum=minimum,
                    maximum=maximum,
                    rule=rule,
                    message=f"Value exceeds the maximum of {maximum}.",
                )
            )

    return failed_records


def _is_comparable_value(
    value: Any,
    minimum: Any,
    maximum: Any,
) -> bool:
    """Check whether the value can be compared with the boundaries."""
    try:
        if minimum is not None:
            value < minimum

        if maximum is not None:
            value > maximum

        return True

    except (TypeError, ValueError):
        return False


def _build_failed_record(
    index: Any,
    value: Any,
    minimum: Any,
    maximum: Any,
    rule: ValidationRule,
    message: str,
) -> FailedRecord:
    """Build a standardized failed-record object."""
    expected_value = _build_expected_value(
        minimum=minimum,
        maximum=maximum,
    )

    return FailedRecord(
        row_number=int(index) + 1,
        column_name=rule.column_name,
        rule_id=rule.rule_id,
        actual_value=value,
        expected_value=expected_value,
        message=message,
    )


def _build_expected_value(
    minimum: Any,
    maximum: Any,
) -> str:
    """Build a readable representation of the expected range."""
    if minimum is not None and maximum is not None:
        return f"{minimum} to {maximum}"

    if minimum is not None:
        return f">= {minimum}"

    return f"<= {maximum}"


def _build_result_message(
    column_name: str,
    minimum: Any,
    maximum: Any,
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    expected_range = _build_expected_value(
        minimum=minimum,
        maximum=maximum,
    )

    if failed_count == 0:
        return (
            f"Range check passed for '{column_name}'. "
            f"Expected range: {expected_range}."
        )

    return (
        f"Range check found {failed_count} invalid "
        f"record(s) in '{column_name}'. "
        f"Expected range: {expected_range}."
    )