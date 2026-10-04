"""
Project : Data Quality Checker
Project ID : 029

Validation Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ValidationRule:
    """Represents one configurable data-quality validation rule."""

    rule_id: str
    column_name: str
    rule_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    severity: str = "FAIL"
    description: str = ""


@dataclass
class FailedRecord:
    """Represents one record that failed a validation rule."""

    row_number: int
    column_name: str
    rule_id: str
    actual_value: Any
    expected_value: Any
    message: str


@dataclass
class ValidationResult:
    """Represents the result of executing one validation rule."""

    rule_id: str
    column_name: str
    rule_type: str
    status: str
    total_records: int
    failed_records: int
    failure_percentage: float
    message: str = ""
    failed_record_details: list[FailedRecord] = field(
        default_factory=list
    )


@dataclass
class ValidationSummary:
    """Represents the complete result of a validation run."""

    dataset_name: str
    file_path: str
    validation_timestamp: datetime = field(
        default_factory=datetime.now
    )
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    total_failed_records: int = 0
    results: list[ValidationResult] = field(
        default_factory=list
    )