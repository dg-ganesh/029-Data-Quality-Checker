"""
Project : Data Quality Checker
Project ID : 029

Profiling Results Repository
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.config import DATABASE_PATH
from src.models.dataset_model import ColumnProfile, DatasetProfile


class ResultsRepository:
    """Provides SQLite persistence for dataset profiling results."""

    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create the profiling tables when they do not exist."""
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS profiling_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    column_count INTEGER NOT NULL,
                    duplicate_row_count INTEGER NOT NULL,
                    profile_timestamp TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS column_profiles (
                    column_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    null_count INTEGER NOT NULL,
                    null_percentage REAL NOT NULL,
                    non_null_count INTEGER NOT NULL,
                    unique_count INTEGER NOT NULL,
                    unique_percentage REAL NOT NULL,
                    minimum_value TEXT,
                    maximum_value TEXT,
                    mean_value TEXT,
                    median_value TEXT,
                    standard_deviation TEXT,
                    most_frequent_value TEXT,
                    most_frequent_count INTEGER NOT NULL,
                    FOREIGN KEY (run_id)
                        REFERENCES profiling_runs (run_id)
                )
                """
            )

    def save_profile(self, profile: DatasetProfile) -> int:
        """
        Persist a complete DatasetProfile.

        Returns:
            The generated profiling run ID.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO profiling_runs (
                    dataset_name,
                    file_path,
                    row_count,
                    column_count,
                    duplicate_row_count,
                    profile_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.dataset_name,
                    profile.file_path,
                    profile.row_count,
                    profile.column_count,
                    profile.duplicate_row_count,
                    profile.profile_timestamp.isoformat(),
                ),
            )

            run_id = int(cursor.lastrowid)

            for column_profile in profile.columns:
                self._save_column_profile(
                    connection,
                    run_id,
                    column_profile,
                )

        return run_id

    def _save_column_profile(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        column_profile: ColumnProfile,
    ) -> None:
        """Persist one column profile belonging to a profiling run."""
        connection.execute(
            """
            INSERT INTO column_profiles (
                run_id,
                column_name,
                data_type,
                null_count,
                null_percentage,
                non_null_count,
                unique_count,
                unique_percentage,
                minimum_value,
                maximum_value,
                mean_value,
                median_value,
                standard_deviation,
                most_frequent_value,
                most_frequent_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                column_profile.column_name,
                column_profile.data_type,
                column_profile.null_count,
                column_profile.null_percentage,
                column_profile.non_null_count,
                column_profile.unique_count,
                column_profile.unique_percentage,
                self._serialize_value(column_profile.minimum),
                self._serialize_value(column_profile.maximum),
                self._serialize_value(column_profile.mean),
                self._serialize_value(column_profile.median),
                self._serialize_value(
                    column_profile.standard_deviation
                ),
                self._serialize_value(
                    column_profile.most_frequent_value
                ),
                column_profile.most_frequent_count,
            ),
        )

    def get_profile_run(self, run_id: int) -> DatasetProfile | None:
        """Retrieve a stored profiling run by its ID."""
        with self._connect() as connection:
            run_row = connection.execute(
                """
                SELECT
                    dataset_name,
                    file_path,
                    row_count,
                    column_count,
                    duplicate_row_count,
                    profile_timestamp
                FROM profiling_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

            if run_row is None:
                return None

            column_rows = connection.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    null_count,
                    null_percentage,
                    non_null_count,
                    unique_count,
                    unique_percentage,
                    minimum_value,
                    maximum_value,
                    mean_value,
                    median_value,
                    standard_deviation,
                    most_frequent_value,
                    most_frequent_count
                FROM column_profiles
                WHERE run_id = ?
                ORDER BY column_profile_id
                """,
                (run_id,),
            ).fetchall()

        columns = [
            self._build_column_profile(row)
            for row in column_rows
        ]

        return DatasetProfile(
            dataset_name=run_row[0],
            file_path=run_row[1],
            row_count=run_row[2],
            column_count=run_row[3],
            duplicate_row_count=run_row[4],
            profile_timestamp=datetime.fromisoformat(run_row[5]),
            columns=columns,
        )

    def list_profile_runs(self) -> list[dict[str, object]]:
        """Return stored profiling runs ordered from newest to oldest."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    run_id,
                    dataset_name,
                    row_count,
                    column_count,
                    duplicate_row_count,
                    profile_timestamp
                FROM profiling_runs
                ORDER BY run_id DESC
                """
            ).fetchall()

        return [
            {
                "run_id": row[0],
                "dataset_name": row[1],
                "row_count": row[2],
                "column_count": row[3],
                "duplicate_row_count": row[4],
                "profile_timestamp": row[5],
            }
            for row in rows
        ]

    @staticmethod
    def _build_column_profile(
        row: tuple,
    ) -> ColumnProfile:
        """Build a ColumnProfile from a SQLite result row."""
        return ColumnProfile(
            column_name=row[0],
            data_type=row[1],
            null_count=row[2],
            null_percentage=row[3],
            non_null_count=row[4],
            unique_count=row[5],
            unique_percentage=row[6],
            minimum=ResultsRepository._deserialize_value(row[7]),
            maximum=ResultsRepository._deserialize_value(row[8]),
            mean=ResultsRepository._deserialize_value(row[9]),
            median=ResultsRepository._deserialize_value(row[10]),
            standard_deviation=ResultsRepository._deserialize_value(
                row[11]
            ),
            most_frequent_value=ResultsRepository._deserialize_value(
                row[12]
            ),
            most_frequent_count=row[13],
        )

    @staticmethod
    def _serialize_value(value: object) -> str | None:
        """Serialize a profiling value for SQLite storage."""
        if value is None:
            return None

        return json.dumps(
            value,
            default=str,
        )

    @staticmethod
    def _deserialize_value(value: str | None) -> object:
        """Deserialize a profiling value retrieved from SQLite."""
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def _connect(self) -> sqlite3.Connection:
        """Create a configured SQLite connection."""
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection