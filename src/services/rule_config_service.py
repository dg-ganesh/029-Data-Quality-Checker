"""
Project : Data Quality Checker
Project ID : 029

Validation Rule Configuration Service
"""

import json
from pathlib import Path
from typing import Any

from src.models.validation_model import ValidationRule


class RuleConfigService:
    """Loads and validates configurable data-quality rules."""

    REQUIRED_RULE_FIELDS = {
        "rule_id",
        "column_name",
        "rule_type",
    }

    SUPPORTED_RULE_TYPES = {
        "required",
        "blank",
        "unique",
        "duplicate",
        "datatype",
        "range",
        "format",
        "business_rule",
    }

    SUPPORTED_SEVERITIES = {
        "FAIL",
        "WARNING",
    }

    def load_rules(
        self,
        configuration_path: Path,
    ) -> list[ValidationRule]:
        """
        Load validation rules from a JSON configuration file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration is invalid.
        """
        if not configuration_path.exists():
            raise FileNotFoundError(
                f"Rule configuration not found: {configuration_path}"
            )

        if not configuration_path.is_file():
            raise ValueError(
                f"Rule configuration is not a file: "
                f"{configuration_path}"
            )

        try:
            with configuration_path.open(
                "r",
                encoding="utf-8",
            ) as configuration_file:
                configuration = json.load(configuration_file)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON rule configuration: {error}"
            ) from error

        return self._build_rules(configuration)

    def _build_rules(
        self,
        configuration: Any,
    ) -> list[ValidationRule]:
        """Convert configuration data into ValidationRule objects."""
        if not isinstance(configuration, list):
            raise ValueError(
                "Rule configuration must contain a JSON list."
            )

        rules: list[ValidationRule] = []

        for index, rule_data in enumerate(configuration, start=1):
            if not isinstance(rule_data, dict):
                raise ValueError(
                    f"Rule {index} must be a JSON object."
                )

            self._validate_rule_data(
                rule_data,
                index,
            )

            rules.append(
                ValidationRule(
                    rule_id=str(rule_data["rule_id"]),
                    column_name=str(rule_data["column_name"]),
                    rule_type=str(rule_data["rule_type"]).lower(),
                    parameters=dict(
                        rule_data.get("parameters", {})
                    ),
                    severity=str(
                        rule_data.get("severity", "FAIL")
                    ).upper(),
                    description=str(
                        rule_data.get("description", "")
                    ),
                )
            )

        return rules

    def _validate_rule_data(
        self,
        rule_data: dict[str, Any],
        rule_number: int,
    ) -> None:
        """Validate the structure and values of one rule."""
        missing_fields = self.REQUIRED_RULE_FIELDS.difference(
            rule_data.keys()
        )

        if missing_fields:
            missing = ", ".join(
                sorted(missing_fields)
            )
            raise ValueError(
                f"Rule {rule_number} is missing required fields: "
                f"{missing}"
            )

        rule_type = str(
            rule_data["rule_type"]
        ).lower()

        if rule_type not in self.SUPPORTED_RULE_TYPES:
            supported_types = ", ".join(
                sorted(self.SUPPORTED_RULE_TYPES)
            )
            raise ValueError(
                f"Unsupported rule type '{rule_type}' in "
                f"rule {rule_number}. "
                f"Supported types: {supported_types}"
            )

        severity = str(
            rule_data.get("severity", "FAIL")
        ).upper()

        if severity not in self.SUPPORTED_SEVERITIES:
            supported_severities = ", ".join(
                sorted(self.SUPPORTED_SEVERITIES)
            )
            raise ValueError(
                f"Unsupported severity '{severity}' in "
                f"rule {rule_number}. "
                f"Supported severities: {supported_severities}"
            )

        parameters = rule_data.get(
            "parameters",
            {},
        )

        if not isinstance(parameters, dict):
            raise ValueError(
                f"Parameters for rule {rule_number} "
                f"must be a JSON object."
            )

    def get_rule_types(self) -> set[str]:
        """Return the supported validation rule types."""
        return set(self.SUPPORTED_RULE_TYPES)

    def get_severities(self) -> set[str]:
        """Return the supported validation severities."""
        return set(self.SUPPORTED_SEVERITIES)