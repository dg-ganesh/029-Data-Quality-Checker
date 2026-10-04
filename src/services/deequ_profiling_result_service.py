"""
Project : Data Quality Checker
Project ID : 029

Deequ Profiling Result Service
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class DeequProfilingResultService:
    """Persist AWS Deequ profiling metrics in SQLite."""

    TABLE_NAME = "deequ_profiling_results"

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        """Initialize the profiling result service."""
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        """Create the profiling result table if required."""
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profiling_timestamp TEXT NOT NULL,
                    metric_entity TEXT,
                    instance TEXT,
                    name TEXT,
                    value TEXT
                )
                """
            )

            connection.commit()

    def save_results(
        self,
        result: dict[str, Any],
    ) -> int:
        """
        Persist Deequ profiling metrics.

        Returns the number of metrics saved.
        """
        self.initialize()

        profiling_timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        metrics = result.get(
            "metrics",
            [],
        )

        rows = []

        for metric in metrics:
            rows.append(
                (
                    profiling_timestamp,
                    self._to_text(
                        metric.get("entity")
                    ),
                    self._to_text(
                        metric.get("instance")
                    ),
                    self._to_text(
                        metric.get("name")
                    ),
                    self._to_text(
                        metric.get("value")
                    ),
                )
            )

        if not rows:
            return 0

        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                f"""
                INSERT INTO {self.TABLE_NAME} (
                    profiling_timestamp,
                    metric_entity,
                    instance,
                    name,
                    value
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

            connection.commit()

        return len(rows)

    def get_results(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return the most recent Deequ profiling metrics."""
        self.initialize()

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                f"""
                SELECT
                    id,
                    profiling_timestamp,
                    metric_entity,
                    instance,
                    name,
                    value
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
    def _to_text(
        value: Any,
    ) -> str | None:
        """Convert a metric value into SQLite-compatible text."""
        if value is None:
            return None

        return str(value)


__all__ = ["DeequProfilingResultService"]