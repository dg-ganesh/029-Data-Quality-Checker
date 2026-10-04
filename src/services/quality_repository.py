"""
Project : Data Quality Checker
Project ID : 029

Quality Results Repository
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import DATABASE_PATH
from src.models.quality_model import (
    ColumnQualityScore,
    QualityCategoryScore,
    QualityComparison,
    QualitySummary,
    RuleQualityScore,
)


class QualityRepository:
    """Provides SQLite persistence for quality assessments."""

    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ):
        self.database_path = database_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create or upgrade quality tables."""

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_run_id INTEGER,
                    dataset_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    total_rules INTEGER NOT NULL,
                    passed_rules INTEGER NOT NULL,
                    failed_rules INTEGER NOT NULL,
                    warning_rules INTEGER NOT NULL,
                    total_failed_records INTEGER NOT NULL,
                    calculation_timestamp TEXT NOT NULL,
                    FOREIGN KEY (
                        validation_run_id
                    ) REFERENCES validation_runs(id)
                )
                """
            )

            self._ensure_validation_run_column(
                connection
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_column_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quality_summary_id INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    total_rules INTEGER NOT NULL,
                    passed_rules INTEGER NOT NULL,
                    failed_rules INTEGER NOT NULL,
                    warning_rules INTEGER NOT NULL,
                    total_failed_records INTEGER NOT NULL,
                    score REAL NOT NULL,
                    FOREIGN KEY (
                        quality_summary_id
                    ) REFERENCES quality_summaries(id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_rule_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quality_summary_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_records INTEGER NOT NULL,
                    failed_records INTEGER NOT NULL,
                    failure_percentage REAL NOT NULL,
                    score REAL NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT,
                    FOREIGN KEY (
                        quality_summary_id
                    ) REFERENCES quality_summaries(id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_category_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quality_summary_id INTEGER NOT NULL,
                    category_name TEXT NOT NULL,
                    total_rules INTEGER NOT NULL,
                    failed_rules INTEGER NOT NULL,
                    total_failed_records INTEGER NOT NULL,
                    score REAL NOT NULL,
                    FOREIGN KEY (
                        quality_summary_id
                    ) REFERENCES quality_summaries(id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    current_run_id INTEGER NOT NULL,
                    previous_run_id INTEGER NOT NULL,
                    current_score REAL NOT NULL,
                    previous_score REAL NOT NULL,
                    score_change REAL NOT NULL,
                    new_failures TEXT,
                    resolved_failures TEXT,
                    improved_columns TEXT,
                    deteriorated_columns TEXT,
                    schema_changes TEXT,
                    comparison_timestamp TEXT NOT NULL
                )
                """
            )

            connection.commit()

    @staticmethod
    def _ensure_validation_run_column(
        connection: sqlite3.Connection,
    ) -> None:
        """Add validation_run_id to existing quality tables."""

        columns = connection.execute(
            """
            PRAGMA table_info(quality_summaries)
            """
        ).fetchall()

        column_names = {
            column[1]
            for column in columns
        }

        if "validation_run_id" not in column_names:
            connection.execute(
                """
                ALTER TABLE quality_summaries
                ADD COLUMN validation_run_id INTEGER
                """
            )

    def save_quality_summary(
        self,
        summary: QualitySummary,
        validation_run_id: int | None = None,
    ) -> int:
        """Persist a complete quality summary."""

        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO quality_summaries (
                    validation_run_id,
                    dataset_name,
                    file_path,
                    quality_score,
                    total_rules,
                    passed_rules,
                    failed_rules,
                    warning_rules,
                    total_failed_records,
                    calculation_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation_run_id,
                    summary.dataset_name,
                    summary.file_path,
                    summary.quality_score,
                    summary.total_rules,
                    summary.passed_rules,
                    summary.failed_rules,
                    summary.warning_rules,
                    summary.total_failed_records,
                    summary.calculation_timestamp.isoformat(),
                ),
            )

            quality_summary_id = int(
                cursor.lastrowid
            )

            for column_score in summary.column_scores:
                self._save_column_score(
                    connection=connection,
                    quality_summary_id=quality_summary_id,
                    column_score=column_score,
                )

                for rule_score in column_score.rule_scores:
                    self._save_rule_score(
                        connection=connection,
                        quality_summary_id=quality_summary_id,
                        rule_score=rule_score,
                    )

            for category_score in summary.category_scores:
                self._save_category_score(
                    connection=connection,
                    quality_summary_id=quality_summary_id,
                    category_score=category_score,
                )

            connection.commit()

        return quality_summary_id

    def save_comparison(
        self,
        comparison: QualityComparison,
    ) -> int:
        """Persist a quality comparison."""

        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO quality_comparisons (
                    current_run_id,
                    previous_run_id,
                    current_score,
                    previous_score,
                    score_change,
                    new_failures,
                    resolved_failures,
                    improved_columns,
                    deteriorated_columns,
                    schema_changes,
                    comparison_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comparison.current_run_id,
                    comparison.previous_run_id,
                    comparison.current_score,
                    comparison.previous_score,
                    comparison.score_change,
                    self._serialize_list(
                        comparison.new_failures
                    ),
                    self._serialize_list(
                        comparison.resolved_failures
                    ),
                    self._serialize_list(
                        comparison.improved_columns
                    ),
                    self._serialize_list(
                        comparison.deteriorated_columns
                    ),
                    self._serialize_list(
                        comparison.schema_changes
                    ),
                    comparison.comparison_timestamp.isoformat(),
                ),
            )

            connection.commit()

        return int(cursor.lastrowid)

    def get_quality_history(
        self,
        dataset_name: str | None = None,
    ) -> list[dict]:
        """Return persisted quality summaries."""

        query = """
            SELECT
                id,
                validation_run_id,
                dataset_name,
                file_path,
                quality_score,
                total_rules,
                passed_rules,
                failed_rules,
                warning_rules,
                total_failed_records,
                calculation_timestamp
            FROM quality_summaries
        """

        parameters: tuple = ()

        if dataset_name is not None:
            query += " WHERE dataset_name = ?"
            parameters = (dataset_name,)

        query += """
            ORDER BY calculation_timestamp DESC, id DESC
        """

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    def get_quality_summary_by_run(
        self,
        validation_run_id: int,
    ) -> QualitySummary | None:
        """Reconstruct a complete quality summary by validation run."""

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            summary_row = connection.execute(
                """
                SELECT
                    id,
                    validation_run_id,
                    dataset_name,
                    file_path,
                    quality_score,
                    total_rules,
                    passed_rules,
                    failed_rules,
                    warning_rules,
                    total_failed_records,
                    calculation_timestamp
                FROM quality_summaries
                WHERE validation_run_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (validation_run_id,),
            ).fetchone()

            if summary_row is None:
                return None

            summary_id = summary_row["id"]

            column_rows = connection.execute(
                """
                SELECT
                    column_name,
                    total_rules,
                    passed_rules,
                    failed_rules,
                    warning_rules,
                    total_failed_records,
                    score
                FROM quality_column_scores
                WHERE quality_summary_id = ?
                ORDER BY id
                """,
                (summary_id,),
            ).fetchall()

            rule_rows = connection.execute(
                """
                SELECT
                    rule_id,
                    column_name,
                    rule_type,
                    status,
                    total_records,
                    failed_records,
                    failure_percentage,
                    score,
                    severity,
                    message
                FROM quality_rule_scores
                WHERE quality_summary_id = ?
                ORDER BY id
                """,
                (summary_id,),
            ).fetchall()

            category_rows = connection.execute(
                """
                SELECT
                    category_name,
                    total_rules,
                    failed_rules,
                    total_failed_records,
                    score
                FROM quality_category_scores
                WHERE quality_summary_id = ?
                ORDER BY id
                """,
                (summary_id,),
            ).fetchall()

        rule_scores = [
            RuleQualityScore(
                rule_id=row["rule_id"],
                column_name=row["column_name"],
                rule_type=row["rule_type"],
                status=row["status"],
                total_records=row["total_records"],
                failed_records=row["failed_records"],
                failure_percentage=row["failure_percentage"],
                score=row["score"],
                severity=row["severity"],
                message=row["message"] or "",
            )
            for row in rule_rows
        ]

        rule_map: dict[str, list[RuleQualityScore]] = {}

        for rule_score in rule_scores:
            rule_map.setdefault(
                rule_score.column_name,
                [],
            ).append(rule_score)

        column_scores = []

        for row in column_rows:
            column_scores.append(
                ColumnQualityScore(
                    column_name=row["column_name"],
                    total_rules=row["total_rules"],
                    passed_rules=row["passed_rules"],
                    failed_rules=row["failed_rules"],
                    warning_rules=row["warning_rules"],
                    total_failed_records=row[
                        "total_failed_records"
                    ],
                    score=row["score"],
                    rule_scores=rule_map.get(
                        row["column_name"],
                        [],
                    ),
                )
            )

        category_scores = [
            QualityCategoryScore(
                category_name=row["category_name"],
                total_rules=row["total_rules"],
                failed_rules=row["failed_rules"],
                total_failed_records=row[
                    "total_failed_records"
                ],
                score=row["score"],
            )
            for row in category_rows
        ]

        return QualitySummary(
            dataset_name=summary_row["dataset_name"],
            file_path=summary_row["file_path"],
            quality_score=summary_row["quality_score"],
            total_rules=summary_row["total_rules"],
            passed_rules=summary_row["passed_rules"],
            failed_rules=summary_row["failed_rules"],
            warning_rules=summary_row["warning_rules"],
            total_failed_records=summary_row[
                "total_failed_records"
            ],
            column_scores=column_scores,
            category_scores=category_scores,
            calculation_timestamp=self._parse_timestamp(
                summary_row["calculation_timestamp"]
            ),
        )

    @staticmethod
    def _parse_timestamp(
        value: str,
    ) -> datetime:
        """Convert persisted timestamp text to datetime."""

        return datetime.fromisoformat(value)

    def get_comparison_history(
        self,
        limit: int = 20,
    ) -> list[dict]:
        """Return recent quality comparisons."""

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    id,
                    current_run_id,
                    previous_run_id,
                    current_score,
                    previous_score,
                    score_change,
                    new_failures,
                    resolved_failures,
                    improved_columns,
                    deteriorated_columns,
                    schema_changes,
                    comparison_timestamp
                FROM quality_comparisons
                ORDER BY comparison_timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    @staticmethod
    def _save_column_score(
        connection: sqlite3.Connection,
        quality_summary_id: int,
        column_score: ColumnQualityScore,
    ) -> None:
        """Persist one column quality score."""

        connection.execute(
            """
            INSERT INTO quality_column_scores (
                quality_summary_id,
                column_name,
                total_rules,
                passed_rules,
                failed_rules,
                warning_rules,
                total_failed_records,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quality_summary_id,
                column_score.column_name,
                column_score.total_rules,
                column_score.passed_rules,
                column_score.failed_rules,
                column_score.warning_rules,
                column_score.total_failed_records,
                column_score.score,
            ),
        )

    @staticmethod
    def _save_rule_score(
        connection: sqlite3.Connection,
        quality_summary_id: int,
        rule_score: RuleQualityScore,
    ) -> None:
        """Persist one rule quality score."""

        connection.execute(
            """
            INSERT INTO quality_rule_scores (
                quality_summary_id,
                rule_id,
                column_name,
                rule_type,
                status,
                total_records,
                failed_records,
                failure_percentage,
                score,
                severity,
                message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quality_summary_id,
                rule_score.rule_id,
                rule_score.column_name,
                rule_score.rule_type,
                rule_score.status,
                rule_score.total_records,
                rule_score.failed_records,
                rule_score.failure_percentage,
                rule_score.score,
                rule_score.severity,
                rule_score.message,
            ),
        )

    @staticmethod
    def _save_category_score(
        connection: sqlite3.Connection,
        quality_summary_id: int,
        category_score: QualityCategoryScore,
    ) -> None:
        """Persist one quality category score."""

        connection.execute(
            """
            INSERT INTO quality_category_scores (
                quality_summary_id,
                category_name,
                total_rules,
                failed_rules,
                total_failed_records,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                quality_summary_id,
                category_score.category_name,
                category_score.total_rules,
                category_score.failed_rules,
                category_score.total_failed_records,
                category_score.score,
            ),
        )

    @staticmethod
    def _serialize_list(
        values: list[str],
    ) -> str:
        """Serialize a list for SQLite text storage."""

        return json.dumps(
            values,
            ensure_ascii=False,
        )