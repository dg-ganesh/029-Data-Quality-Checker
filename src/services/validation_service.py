"""
Project : Data Quality Checker
Project ID : 029

Validation Service
"""

from pathlib import Path

import pandas as pd

from src.core.validation.blank_check import validate_blank
from src.core.validation.business_rule_check import (
    validate_business_rule,
)
from src.core.validation.datatype_check import validate_datatype
from src.core.validation.duplicate_check import validate_duplicate
from src.core.validation.format_check import validate_format
from src.core.validation.range_check import validate_range
from src.core.validation.required_check import validate_required
from src.core.validation.validation_engine import ValidationEngine
from src.models.validation_model import (
    ValidationRule,
    ValidationSummary,
)
from src.services.results_repository import ResultsRepository
from src.services.rule_config_service import RuleConfigService
from src.services.validation_repository import ValidationRepository


class ValidationService:
    """Coordinates dataset validation and result persistence."""

    def __init__(
        self,
        rule_config_service: RuleConfigService,
        validation_repository: ValidationRepository,
        results_repository: ResultsRepository,
    ):
        self.rule_config_service = rule_config_service
        self.validation_repository = validation_repository
        self.results_repository = results_repository

    def validate_dataset(
        self,
        dataframe: pd.DataFrame,
        dataset_name: str,
        file_path: Path,
        configuration_path: Path,
    ) -> ValidationSummary:
        """Execute all configured validation rules."""
        rules = self.rule_config_service.load_rules(
            configuration_path
        )

        engine = self._build_validation_engine()

        results = engine.validate(
            dataframe=dataframe,
            rules=rules,
        )

        summary = self._build_summary(
            dataset_name=dataset_name,
            file_path=file_path,
            rules=rules,
            results=results,
        )

        self.validation_repository.save_validation(
            summary
        )

        return summary

    @staticmethod
    def _build_validation_engine() -> ValidationEngine:
        """Create and configure the validation engine."""
        engine = ValidationEngine()

        engine.register_validator(
            "required",
            validate_required,
        )

        engine.register_validator(
            "blank",
            validate_blank,
        )

        engine.register_validator(
            "unique",
            validate_duplicate,
        )

        engine.register_validator(
            "duplicate",
            validate_duplicate,
        )

        engine.register_validator(
            "datatype",
            validate_datatype,
        )

        engine.register_validator(
            "range",
            validate_range,
        )

        engine.register_validator(
            "format",
            validate_format,
        )

        engine.register_validator(
            "business_rule",
            validate_business_rule,
        )

        return engine

    @staticmethod
    def _build_summary(
        dataset_name: str,
        file_path: Path,
        rules: list[ValidationRule],
        results,
    ) -> ValidationSummary:
        """Build the overall validation summary."""
        passed_rules = sum(
            1
            for result in results
            if result.status == "PASS"
        )

        failed_rules = sum(
            1
            for result in results
            if result.status == "FAIL"
        )

        warning_rules = sum(
            1
            for result in results
            if result.status == "WARNING"
        )

        total_failed_records = sum(
            result.failed_records
            for result in results
        )

        return ValidationSummary(
            dataset_name=dataset_name,
            file_path=str(file_path),
            total_rules=len(rules),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warning_rules=warning_rules,
            total_failed_records=total_failed_records,
            results=results,
        )