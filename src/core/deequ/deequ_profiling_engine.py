"""
Project : Data Quality Checker
Project ID : 029

Deequ Profiling Engine
"""

from __future__ import annotations

from typing import Any

from pyspark.sql import DataFrame, SparkSession

from pydeequ.analyzers import (
    AnalysisRunner,
    AnalyzerContext,
    ApproxCountDistinct,
    Completeness,
    Maximum,
    Mean,
    Minimum,
    Size,
)


class DeequProfilingEngine:
    """Execute AWS Deequ analyzers against a Spark DataFrame."""

    def __init__(
        self,
        spark: SparkSession,
    ) -> None:
        """Initialize the profiling engine with a Spark session."""
        self.spark = spark

    def profile(
        self,
        dataframe: DataFrame,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Deequ profiling analyzers and return metric records.

        When columns are not supplied, all DataFrame columns are profiled.
        """
        selected_columns = columns or dataframe.columns

        analyzers = self._build_analyzers(
            dataframe,
            selected_columns,
        )

        runner = (
            AnalysisRunner(self.spark)
            .onData(dataframe)
        )

        for analyzer in analyzers:
            runner = runner.addAnalyzer(
                analyzer
            )

        analysis_result = runner.run()

        metrics_dataframe = (
            AnalyzerContext.successMetricsAsDataFrame(
                self.spark,
                analysis_result,
            )
        )

        return {
            "row_count": dataframe.count(),
            "metrics": self._collect_metrics(
                metrics_dataframe
            ),
        }

    def _build_analyzers(
        self,
        dataframe: DataFrame,
        columns: list[str],
    ) -> list[Any]:
        """Build the applicable Deequ analyzers for the DataFrame."""
        analyzers: list[Any] = [
            Size()
        ]

        for column in columns:
            analyzers.extend(
                [
                    Completeness(column),
                    ApproxCountDistinct(column),
                ]
            )

            if self._is_numeric_column(
                dataframe,
                column,
            ):
                analyzers.extend(
                    [
                        Minimum(column),
                        Maximum(column),
                        Mean(column),
                    ]
                )

        return analyzers

    @staticmethod
    def _is_numeric_column(
        dataframe: DataFrame,
        column: str,
    ) -> bool:
        """Return whether a Spark DataFrame column is numeric."""
        numeric_types = {
            "byte",
            "short",
            "int",
            "long",
            "float",
            "double",
            "decimal",
        }

        return (
            dataframe.schema[column]
            .dataType
            .simpleString()
            .lower()
            in numeric_types
        )

    @staticmethod
    def _collect_metrics(
        metrics_dataframe: DataFrame,
    ) -> list[dict[str, Any]]:
        """Convert successful Deequ metrics into Python dictionaries."""
        return [
            row.asDict(
                recursive=True
            )
            for row in metrics_dataframe.collect()
        ]


__all__ = [
    "DeequProfilingEngine"
]