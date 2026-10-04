"""
Project : Data Quality Checker
Project ID : 029

Duplicate-Value Validation
"""

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


def validate_duplicate(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate that duplicate records do not exist in the dataset.

    A duplicate record is a row whose complete set of column values
    matches another row in the dataset.
    """
    duplicate_mask = dataframe.duplicated(
        keep=False
    )

    failed_records = _build_failed_records(
        dataframe=dataframe,
        duplicate_mask=duplicate_mask,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(dataframe),
        failed_records=failed_records,
        message=_build_result_message(
            failed_count=len(failed_records),
        ),
    )


def _build_failed_records(
    dataframe: pd.DataFrame,
    duplicate_mask: pd.Series,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for duplicate rows."""
    failed_records: list[FailedRecord] = []

    for index in dataframe.index[duplicate_mask]:
        row = dataframe.loc[index]

        failed_records.append(
            FailedRecord(
                row_number=int(index) + 1,
                column_name="__ROW__",
                rule_id=rule.rule_id,
                actual_value=_serialize_row(row),
                expected_value="Unique record",
                message="Duplicate record detected.",
            )
        )

    return failed_records


def _serialize_row(row: pd.Series) -> dict:
    """Convert a DataFrame row into a serializable dictionary."""
    serialized: dict = {}

    for column_name, value in row.items():
        if pd.isna(value):
            serialized[column_name] = None
        else:
            serialized[column_name] = value

    return serialized


def _build_result_message(
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    if failed_count == 0:
        return "Duplicate-record check passed."

    return (
        f"Duplicate-record check found "
        f"{failed_count} duplicate record(s)."
    )