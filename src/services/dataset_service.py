"""
Project : Data Quality Checker
Project ID : 029

Deequ Spark Service
"""

from __future__ import annotations

import os

from pyspark.sql import SparkSession


class DeequService:
    """Manage the Spark session used by AWS Deequ."""

    SPARK_VERSION = "4.1"

    DEEQU_MAVEN_COORDINATE = (
        "com.amazon.deequ:deequ:2.0.18-spark-4.1"
    )

    def __init__(self) -> None:
        """Initialize the Deequ service configuration."""
        self.spark: SparkSession | None = None

    def start(self) -> SparkSession:
        """Start and return the Spark session configured for Deequ."""
        os.environ["SPARK_VERSION"] = self.SPARK_VERSION

        if self.spark is not None:
            return self.spark

        self.spark = (
            SparkSession.builder
            .appName("DataQualityChecker-Deequ")
            .config(
                "spark.jars.packages",
                self.DEEQU_MAVEN_COORDINATE,
            )
            .config(
                "spark.sql.shuffle.partitions",
                "4",
            )
            .getOrCreate()
        )

        return self.spark

    def health_check(self) -> dict[str, str]:
        """Verify that Spark and the Deequ configuration are available."""
        spark = self.start()

        return {
            "spark_version": spark.version,
            "spark_version_target": self.SPARK_VERSION,
            "deequ_maven_coordinate": (
                self.DEEQU_MAVEN_COORDINATE
            ),
            "status": "PASS",
        }

    def stop(self) -> None:
        """Stop the Spark session and release Spark resources."""
        if self.spark is None:
            return

        try:
            self.spark.stop()
        finally:
            self.spark = None


__all__ = ["DeequService"]