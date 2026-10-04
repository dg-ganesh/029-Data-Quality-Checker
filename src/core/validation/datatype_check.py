"""
Project : Data Quality Checker
Project ID : 029

Data-Type Validation
"""

from datetime import date, datetime

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


SUPPORTED_DATA_TYPES = {
    "string",
    "integer",
    "float",
    "number",
    "boolean",
    "date",
    "datetime",
}


def validate_datatype(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate that values in a configured column match the
    expected data type.
    """
    column_name = rule.column_name
    expected_type = str(
        rule.parameters.get("expected_type", "")
    ).lower().strip()

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Datatype check column '{column_name}' "
                "does not exist in the dataset."
            ),
        )

    if expected_type not in SUPPORTED_DATA_TYPES:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Unsupported expected data type "
                f"'{expected_type}' for column "
                f"'{column_name}'."
            ),
        )

    series = dataframe[column_name]

    failed_records = _build_failed_records(
        series=series,
        expected_type=expected_type,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(series),
        failed_records=failed_records,
        message=_build_result_message(
            column_name=column_name,
            expected_type=expected_type,
            failed_count=len(failed_records),
        ),
    )


def _build_failed_records(
    series: pd.Series,
    expected_type: str,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for invalid data types."""
    failed_records: list[FailedRecord] = []

    for index, value in series.items():
        if pd.isna(value):
            continue

        if not _is_valid_type(value, expected_type):
            failed_records.append(
                FailedRecord(
                    row_number=int(index) + 1,
                    column_name=rule.column_name,
                    rule_id=rule.rule_id,
                    actual_value=value,
                    expected_value=expected_type,
                    message=(
                        f"Value in '{rule.column_name}' "
                        f"does not match expected type "
                        f"'{expected_type}'."
                    ),
                )
            )

    return failed_records


def _is_valid_type(
    value,
    expected_type: str,
) -> bool:
    """Determine whether a value matches the expected type."""
    if expected_type == "string":
        return isinstance(value, str)

    if expected_type == "integer":
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        )

    if expected_type in {"float", "number"}:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    if expected_type == "boolean":
        return isinstance(value, bool)

    if expected_type == "date":
        return isinstance(value, date) and not isinstance(
            value,
            datetime,
        )

    if expected_type == "datetime":
        return isinstance(value, datetime)

    return False


def _build_result_message(
    column_name: str,
    expected_type: str,
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    if failed_count == 0:
        return (
            f"Datatype check passed for '{column_name}' "
            f"as '{expected_type}'."
        )

    return (
        f"Datatype check found {failed_count} invalid "
        f"record(s) in '{column_name}'. Expected type: "
        f"'{expected_type}'."
    )
