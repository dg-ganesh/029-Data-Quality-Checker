"""
Project : Data Quality Checker
Project ID : 029

Validation Results Repository
"""

import json
import sqlite3
from pathlib import Path

from src.models.validation_model import (
    FailedRecord,
    ValidationResult,
    ValidationSummary,
)
from src.config import DATABASE_PATH


class ValidationRepository:
    """Provides SQLite persistence for validation results."""

    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = database_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create validation tables when they do not exist."""
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    validation_timestamp TEXT NOT NULL,
                    total_rules INTEGER NOT NULL,
                    passed_rules INTEGER NOT NULL,
                    failed_rules INTEGER NOT NULL,
                    warning_rules INTEGER NOT NULL,
                    total_failed_records INTEGER NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_run_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_records INTEGER NOT NULL,
                    failed_records INTEGER NOT NULL,
                    failure_percentage REAL NOT NULL,
                    message TEXT,
                    FOREIGN KEY (
                        validation_run_id
                    ) REFERENCES validation_runs(id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS failed_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_result_id INTEGER NOT NULL,
                    row_number INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    actual_value TEXT,
                    expected_value TEXT,
                    message TEXT,
                    FOREIGN KEY (
                        validation_result_id
                    ) REFERENCES validation_results(id)
                )
                """
            )

            connection.commit()

    def save_validation(
        self,
        summary: ValidationSummary,
    ) -> int:
        """Persist a complete validation summary."""
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO validation_runs (
                    dataset_name,
                    file_path,
                    validation_timestamp,
                    total_rules,
                    passed_rules,
                    failed_rules,
                    warning_rules,
                    total_failed_records
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.dataset_name,
                    summary.file_path,
                    summary.validation_timestamp.isoformat(),
                    summary.total_rules,
                    summary.passed_rules,
                    summary.failed_rules,
                    summary.warning_rules,
                    summary.total_failed_records,
                ),
            )

            validation_run_id = cursor.lastrowid

            for result in summary.results:
                validation_result_id = self._save_result(
                    connection=connection,
                    validation_run_id=validation_run_id,
                    result=result,
                )

                self._save_failed_records(
                    connection=connection,
                    validation_result_id=validation_result_id,
                    failed_records=result.failed_record_details,
                )

            connection.commit()

        return int(validation_run_id)

    def _save_result(
        self,
        connection: sqlite3.Connection,
        validation_run_id: int,
        result: ValidationResult,
    ) -> int:
        """Persist one validation result."""
        cursor = connection.execute(
            """
            INSERT INTO validation_results (
                validation_run_id,
                rule_id,
                column_name,
                rule_type,
                status,
                total_records,
                failed_records,
                failure_percentage,
                message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                validation_run_id,
                result.rule_id,
                result.column_name,
                result.rule_type,
                result.status,
                result.total_records,
                result.failed_records,
                result.failure_percentage,
                result.message,
            ),
        )

        return int(cursor.lastrowid)

    def _save_failed_records(
        self,
        connection: sqlite3.Connection,
        validation_result_id: int,
        failed_records: list[FailedRecord],
    ) -> None:
        """Persist failed-record details."""
        for failed_record in failed_records:
            connection.execute(
                """
                INSERT INTO failed_records (
                    validation_result_id,
                    row_number,
                    column_name,
                    rule_id,
                    actual_value,
                    expected_value,
                    message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation_result_id,
                    failed_record.row_number,
                    failed_record.column_name,
                    failed_record.rule_id,
                    self._serialize_value(
                        failed_record.actual_value
                    ),
                    self._serialize_value(
                        failed_record.expected_value
                    ),
                    failed_record.message,
                ),
            )

    @staticmethod
    def _serialize_value(value) -> str | None:
        """Convert a value into SQLite-safe text."""
        if value is None:
            return None

        if isinstance(value, (dict, list, tuple)):
            return json.dumps(
                value,
                default=str,
            )

        return str(value)