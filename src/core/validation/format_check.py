"""
Project : Data Quality Checker
Project ID : 029

Format Validation
"""

import re
from typing import Callable

import pandas as pd

from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


FORMAT_PATTERNS: dict[str, str] = {
    "email": (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
        r"[A-Za-z0-9])?(?:\.[A-Za-z0-9]"
        r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
    ),
    "phone": r"^\+?[0-9][0-9\s().-]{7,20}$",
    "date_iso": r"^\d{4}-\d{2}-\d{2}$",
    "postal_code": r"^\d{5,10}$",
}


def validate_format(
    dataframe: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationResult:
    """
    Validate values against a configured format.

    Supported parameters:
        format_type
        pattern

    format_type may refer to a built-in pattern such as:
        email
        phone
        date_iso
        postal_code

    A custom regular expression may be supplied through:
        pattern
    """
    column_name = rule.column_name

    if column_name not in dataframe.columns:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Format check column '{column_name}' "
                "does not exist in the dataset."
            ),
        )

    pattern, format_description = _resolve_pattern(rule)

    if pattern is None:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Format configuration for '{column_name}' "
                "does not contain a supported format_type "
                "or pattern."
            ),
        )

    try:
        compiled_pattern = re.compile(pattern)
    except re.error as error:
        return ValidationEngine.build_result(
            rule=rule,
            total_records=len(dataframe),
            failed_records=[],
            message=(
                f"Invalid regular expression for "
                f"'{column_name}': {error}"
            ),
        )

    failed_records = _build_failed_records(
        series=dataframe[column_name],
        compiled_pattern=compiled_pattern,
        format_description=format_description,
        rule=rule,
    )

    return ValidationEngine.build_result(
        rule=rule,
        total_records=len(dataframe),
        failed_records=failed_records,
        message=_build_result_message(
            column_name=column_name,
            format_description=format_description,
            failed_count=len(failed_records),
        ),
    )


def _resolve_pattern(
    rule: ValidationRule,
) -> tuple[str | None, str]:
    """Resolve a built-in or custom format pattern."""
    parameters = rule.parameters

    custom_pattern = parameters.get("pattern")

    if custom_pattern:
        return str(custom_pattern), "custom pattern"

    format_type = str(
        parameters.get("format_type", "")
    ).lower().strip()

    if format_type in FORMAT_PATTERNS:
        return FORMAT_PATTERNS[format_type], format_type

    return None, ""


def _build_failed_records(
    series: pd.Series,
    compiled_pattern: re.Pattern,
    format_description: str,
    rule: ValidationRule,
) -> list[FailedRecord]:
    """Create failed-record details for invalid formats."""
    failed_records: list[FailedRecord] = []

    for index, value in series.items():
        if pd.isna(value):
            continue

        string_value = str(value)

        if compiled_pattern.fullmatch(string_value) is None:
            failed_records.append(
                FailedRecord(
                    row_number=int(index) + 1,
                    column_name=rule.column_name,
                    rule_id=rule.rule_id,
                    actual_value=value,
                    expected_value=format_description,
                    message=(
                        f"Value in '{rule.column_name}' "
                        f"does not match the expected "
                        f"{format_description}."
                    ),
                )
            )

    return failed_records


def _build_result_message(
    column_name: str,
    format_description: str,
    failed_count: int,
) -> str:
    """Build a human-readable validation result message."""
    if failed_count == 0:
        return (
            f"Format check passed for '{column_name}' "
            f"using {format_description}."
        )

    return (
        f"Format check found {failed_count} invalid "
        f"record(s) in '{column_name}' using "
        f"{format_description}."
    )