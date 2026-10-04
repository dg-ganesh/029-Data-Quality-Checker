"""
Project : Data Quality Checker
Project ID : 029

Deequ Result Service
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class DeequResultService:
    """Persist AWS Deequ validation results in SQLite."""

    TABLE_NAME = "deequ_validation_results"

    def __init__(self, database_path: str | Path) -> None:
        """Initialize the result service with the SQLite database path."""
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        """Create the Deequ result table when it does not exist."""
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_timestamp TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    check_name TEXT,
                    check_level TEXT,
                    check_status TEXT,
                    constraint_name TEXT,
                    constraint_status TEXT,
                    constraint_message TEXT,
                    metric_value TEXT
                )
                """
            )

            connection.commit()

    def save_results(
        self,
        result: dict[str, Any],
    ) -> int:
        """
        Persist a Deequ validation result.

        Returns the number of constraint records saved.
        """
        self.initialize()

        validation_timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        overall_status = str(
            result.get(
                "status",
                "UNKNOWN",
            )
        )

        constraints = result.get(
            "constraints",
            [],
        )

        rows = []

        for constraint in constraints:
            rows.append(
                (
                    validation_timestamp,
                    overall_status,
                    self._to_text(
                        constraint.get("check")
                    ),
                    self._to_text(
                        constraint.get("check_level")
                    ),
                    self._to_text(
                        constraint.get("check_status")
                    ),
                    self._to_text(
                        constraint.get("constraint")
                    ),
                    self._to_text(
                        constraint.get("constraint_status")
                    ),
                    self._to_text(
                        constraint.get("constraint_message")
                    ),
                    self._to_text(
                        constraint.get("metric_value")
                    ),
                )
            )

        if not rows:
            return 0

        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                f"""
                INSERT INTO {self.TABLE_NAME} (
                    validation_timestamp,
                    overall_status,
                    check_name,
                    check_level,
                    check_status,
                    constraint_name,
                    constraint_status,
                    constraint_message,
                    metric_value
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            connection.commit()

        return len(rows)

    def get_results(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return the most recent persisted Deequ results."""
        self.initialize()

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                f"""
                SELECT
                    id,
                    validation_timestamp,
                    overall_status,
                    check_name,
                    check_level,
                    check_status,
                    constraint_name,
                    constraint_status,
                    constraint_message,
                    metric_value
                FROM {self.TABLE_NAME}
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    @staticmethod
    def _to_text(value: Any) -> str | None:
        """Convert a result value into SQLite-compatible text."""
        if value is None:
            return None

        return str(value)


__all__ = ["DeequResultService"]