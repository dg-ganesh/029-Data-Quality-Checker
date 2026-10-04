"""
Project : Data Quality Checker
Project ID : 029

Blank-Value Validation
"""

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


def validate_blank(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate that the configured column contains no blank values.

    Blank values include empty strings and strings containing
    only whitespace. Missing values are handled separately by
    the required-field validator.
    """
    column_name = rule.column_name

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Blank-value check column '{column_name}' "
                f"does not exist in the dataset."
            ),
        )

    series = dataframe[column_name]

    blank_mask = _build_blank_mask(series)

    failed_records = _build_failed_records(
        series=series,
        blank_mask=blank_mask,
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


def _build_blank_mask(series: pd.Series) -> pd.Series:
    """Return a Boolean mask identifying blank values."""
    string_values = series.astype("string")

    return (
        string_values.notna()
        & string_values.str.strip().eq("")
    )


def _build_failed_records(
    series: pd.Series,
    blank_mask: pd.Series,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for blank values."""
    failed_records: list[FailedRecord] = []

    for index in series.index[blank_mask]:
        actual_value = series.loc[index]

        failed_records.append(
            FailedRecord(
                row_number=int(index) + 1,
                column_name=rule.column_name,
                rule_id=rule.rule_id,
                actual_value=actual_value,
                expected_value="Non-blank value",
                message=(
                    f"Column '{rule.column_name}' "
                    "contains a blank value."
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
            f"Blank-value check passed for "
            f"'{column_name}'."
        )

    return (
        f"Blank-value check found {failed_count} "
        f"blank record(s) in '{column_name}'."
    )
