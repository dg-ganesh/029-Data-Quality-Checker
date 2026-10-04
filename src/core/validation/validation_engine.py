"""
Project : Data Quality Checker
Project ID : 029

Validation Engine
"""

from collections.abc import Callable

import pandas as pd

from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationRule,
)


class ValidationEngine:
    """Coordinates execution of configured validation rules."""

    def __init__(self) -> None:
        self._validators: dict[
            str,
            Callable[
                [pd.DataFrame, ValidationRule],
                ValidationResult,
            ],
        ] = {}

    def register_validator(
        self,
        rule_type: str,
        validator: Callable[
            [pd.DataFrame, ValidationRule],
            ValidationResult,
        ],
    ) -> None:
        """
        Register a validator for a specific rule type.

        Raises:
            ValueError: If the rule type is empty or already registered.
        """
        normalized_rule_type = rule_type.strip().lower()

        if not normalized_rule_type:
            raise ValueError(
                "Validator rule type cannot be empty."
            )

        if normalized_rule_type in self._validators:
            raise ValueError(
                f"Validator already registered: "
                f"{normalized_rule_type}"
            )

        self._validators[normalized_rule_type] = validator

    def validate(
        self,
        dataframe: pd.DataFrame,
        rules: list[ValidationRule],
    ) -> list[ValidationResult]:
        """
        Execute all supplied validation rules.

        Rules are executed in the order provided.
        """
        results: list[ValidationResult] = []

        for rule in rules:
            results.append(
                self._execute_rule(
                    dataframe,
                    rule,
                )
            )

        return results

    def validate_rule(
        self,
        dataframe: pd.DataFrame,
        rule: ValidationRule,
    ) -> ValidationResult:
        """Execute one validation rule."""
        return self._execute_rule(
            dataframe,
            rule,
        )

    def _execute_rule(
        self,
        dataframe: pd.DataFrame,
        rule: ValidationRule,
    ) -> ValidationResult:
        """Execute a rule through its registered validator."""
        rule_type = rule.rule_type.strip().lower()

        validator = self._validators.get(rule_type)

        if validator is None:
            return self._build_configuration_error(
                dataframe,
                rule,
                (
                    f"No validator registered for "
                    f"rule type '{rule_type}'."
                ),
            )

        try:
            return validator(
                dataframe,
                rule,
            )

        except Exception as error:
            return self._build_execution_error(
                dataframe,
                rule,
                str(error),
            )

    @staticmethod
    def _build_configuration_error(
        dataframe: pd.DataFrame,
        rule: ValidationRule,
        message: str,
    ) -> ValidationResult:
        """Build a failed result for an invalid validator configuration."""
        return ValidationResult(
            rule_id=rule.rule_id,
            column_name=rule.column_name,
            rule_type=rule.rule_type,
            status="FAIL",
            total_records=len(dataframe),
            failed_records=0,
            failure_percentage=0.0,
            message=message,
        )

    @staticmethod
    def _build_execution_error(
        dataframe: pd.DataFrame,
        rule: ValidationRule,
        message: str,
    ) -> ValidationResult:
        """Build a failed result when validator execution errors."""
        return ValidationResult(
            rule_id=rule.rule_id,
            column_name=rule.column_name,
            rule_type=rule.rule_type,
            status="FAIL",
            total_records=len(dataframe),
            failed_records=0,
            failure_percentage=0.0,
            message=(
                f"Validation execution error: {message}"
            ),
        )

    @staticmethod
    def build_result(
        rule: ValidationRule,
        total_records: int,
        failed_records: list[FailedRecord],
        message: str = "",
    ) -> ValidationResult:
        """
        Build a standardized ValidationResult from failed records.
        """
        failure_count = len(failed_records)

        if total_records == 0:
            failure_percentage = 0.0
        else:
            failure_percentage = round(
                (failure_count / total_records) * 100,
                2,
            )

        if failure_count == 0:
            status = "PASS"
        else:
            status = rule.severity.upper()

        return ValidationResult(
            rule_id=rule.rule_id,
            column_name=rule.column_name,
            rule_type=rule.rule_type,
            status=status,
            total_records=total_records,
            failed_records=failure_count,
            failure_percentage=failure_percentage,
            message=message,
            failed_record_details=failed_records,
        )

    def get_registered_rule_types(self) -> list[str]:
        """Return registered validator types."""
        return sorted(self._validators)