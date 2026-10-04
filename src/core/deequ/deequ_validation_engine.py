"""
Project : Data Quality Checker
Project ID : 029

Deequ Validation Engine
"""

from __future__ import annotations

from typing import Any

from pyspark.sql import DataFrame, SparkSession

from pydeequ.checks import Check, CheckLevel
from pydeequ.verification import (
    VerificationResult,
    VerificationSuite,
)


class DeequValidationEngine:
    """Execute AWS Deequ validation checks against a Spark DataFrame."""

    def __init__(self, spark: SparkSession) -> None:
        """Initialize the validation engine with a Spark session."""
        self.spark = spark

    def validate(
        self,
        dataframe: DataFrame,
    ) -> dict[str, Any]:
        """
        Execute the Project 029 Deequ validation rules.

        Returns a dictionary containing the overall verification status
        and individual constraint results.
        """
        check = (
            Check(
                self.spark,
                CheckLevel.Error,
                "Project 029 Data Quality Checks",
            )
            .isComplete(
                "CustomerID",
                hint="CustomerID must not be null",
            )
            .isComplete(
                "Gender",
                hint="Gender must not be null",
            )
            .isComplete(
                "MonthlyCharges",
                hint="MonthlyCharges must not be null",
            )
            .isNonNegative(
                "MonthlyCharges",
                hint="MonthlyCharges must be greater than or equal to zero",
            )
            .hasPattern(
                "CustomerID",
                r"^CUST_[0-9]+$",
                hint="CustomerID must follow the CUST_<number> format",
            )
        )

        verification_result = (
            VerificationSuite(self.spark)
            .onData(dataframe)
            .addCheck(check)
            .run()
        )

        return self._build_result(verification_result)

    def _build_result(
        self,
        verification_result: Any,
    ) -> dict[str, Any]:
        """Convert the Deequ verification result into Python records."""
        result_dataframe = (
            VerificationResult.checkResultsAsDataFrame(
                self.spark,
                verification_result,
            )
        )

        constraints = [
            row.asDict(recursive=True)
            for row in result_dataframe.collect()
        ]

        return {
            "status": str(
                verification_result.status
            ),
            "constraint_count": len(constraints),
            "constraints": constraints,
        }


__all__ = ["DeequValidationEngine"]