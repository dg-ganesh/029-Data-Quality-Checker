"""
Project : Data Quality Checker
Project ID : 029

Quality Scoring Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RuleQualityScore:
    """Represents the quality score for one validation rule."""

    rule_id: str
    column_name: str
    rule_type: str
    status: str
    total_records: int
    failed_records: int
    failure_percentage: float
    score: float
    severity: str = "FAIL"
    message: str = ""


@dataclass
class ColumnQualityScore:
    """Represents the aggregated quality score for one column."""

    column_name: str
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    total_failed_records: int = 0
    score: float = 0.0
    rule_scores: list[RuleQualityScore] = field(
        default_factory=list
    )


@dataclass
class QualityCategoryScore:
    """Represents the quality score for one exception category."""

    category_name: str
    total_rules: int = 0
    failed_rules: int = 0
    total_failed_records: int = 0
    score: float = 0.0


@dataclass
class QualitySummary:
    """Represents the overall quality assessment of a dataset."""

    dataset_name: str
    file_path: str
    quality_score: float
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    total_failed_records: int
    column_scores: list[ColumnQualityScore] = field(
        default_factory=list
    )
    category_scores: list[QualityCategoryScore] = field(
        default_factory=list
    )
    calculation_timestamp: datetime = field(
        default_factory=datetime.now
    )


@dataclass
class QualityComparison:
    """Represents quality changes between two validation runs."""

    current_run_id: int
    previous_run_id: int
    current_score: float
    previous_score: float
    score_change: float
    new_failures: list[str] = field(
        default_factory=list
    )
    resolved_failures: list[str] = field(
        default_factory=list
    )
    improved_columns: list[str] = field(
        default_factory=list
    )
    deteriorated_columns: list[str] = field(
        default_factory=list
    )
    schema_changes: list[str] = field(
        default_factory=list
    )
    comparison_timestamp: datetime = field(
        default_factory=datetime.now
    )