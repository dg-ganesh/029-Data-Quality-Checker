"""
Project : Data Quality Checker
Project ID : 029

Required-Field Validation
"""

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


def validate_required(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate that the configured column contains no missing values.
    """
    column_name = rule.column_name

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Required column '{column_name}' "
                f"does not exist in the dataset."
            ),
        )

    series = dataframe[column_name]
    missing_mask = series.isna()

    failed_records = _build_failed_records(
        series=series,
        missing_mask=missing_mask,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(dataframe),
        failed_records=failed_records,
        message=_build_result_message(
            column_name=column_name,
            failed_count=len(failed_records),
        ),
    )


def _build_failed_records(
    series: pd.Series,
    missing_mask: pd.Series,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for missing values."""
    failed_records: list[FailedRecord] = []

    for index in series.index[missing_mask]:
        failed_records.append(
            FailedRecord(
                row_number=int(index) + 1,
                column_name=rule.column_name,
                rule_id=rule.rule_id,
                actual_value=None,
                expected_value="Non-null value",
                message=(
                    f"Required field '{rule.column_name}' "
                    "contains a missing value."
                ),
            )
        )

    return failed_records


def _build_result_message(
    column_name: str,
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    if failed_count == 0:
        return (
            f"Required-field check passed for "
            f"'{column_name}'."
        )

    return (
        f"Required-field check found {failed_count} "
        f"missing record(s) in '{column_name}'."
    )
