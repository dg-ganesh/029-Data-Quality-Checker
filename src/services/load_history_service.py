"""
Project : Data Quality Checker
Project ID : 029

Load History Service
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.config import DATABASE_PATH
from src.services.validation_repository import ValidationRepository


@dataclass
class LoadHistoryRecord:
    """Represents one historical validation run."""

    run_id: int
    dataset_name: str
    file_path: str
    validation_timestamp: datetime
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    total_failed_records: int


class LoadHistoryService:
    """Provides access to historical validation runs."""

    def __init__(
        self,
        validation_repository: ValidationRepository | None = None,
    ):
        self.validation_repository = (
            validation_repository
            if validation_repository is not None
            else ValidationRepository()
        )

    def get_load_history(
        self,
        dataset_name: str | None = None,
    ) -> list[LoadHistoryRecord]:
        """
        Return validation runs in reverse chronological order.

        When dataset_name is supplied, only runs for that dataset
        are returned.
        """
        runs = self._get_repository_runs()

        history: list[LoadHistoryRecord] = []

        for run in runs:
            if dataset_name is not None:
                if run["dataset_name"] != dataset_name:
                    continue

            history.append(
                self._build_history_record(run)
            )

        return history

    def get_latest_load(
        self,
        dataset_name: str | None = None,
    ) -> LoadHistoryRecord | None:
        """Return the most recent validation run."""
        history = self.get_load_history(
            dataset_name=dataset_name
        )

        if not history:
            return None

        return history[0]

    def get_previous_load(
        self,
        dataset_name: str,
    ) -> LoadHistoryRecord | None:
        """Return the validation run immediately before the latest."""
        history = self.get_load_history(
            dataset_name=dataset_name
        )

        if len(history) < 2:
            return None

        return history[1]

    def get_load_by_id(
        self,
        run_id: int,
    ) -> LoadHistoryRecord | None:
        """Return a specific validation run by ID."""
        runs = self._get_repository_runs()

        for run in runs:
            if int(run["id"]) == run_id:
                return self._build_history_record(run)

        return None

    def get_load_count(
        self,
        dataset_name: str | None = None,
    ) -> int:
        """Return the number of validation runs available."""
        return len(
            self.get_load_history(
                dataset_name=dataset_name
            )
        )

    def _get_repository_runs(self) -> list[dict]:
        """
        Retrieve historical validation runs from the repository.

        The existing Slice 2 repository currently exposes
        persistence operations, so this service uses its database
        path for historical retrieval.
        """
        database_path = self._get_database_path()

        import sqlite3

        if not database_path.exists():
            return []

        with sqlite3.connect(database_path) as connection:
            connection.row_factory = sqlite3.Row

            cursor = connection.execute(
                """
                SELECT
                    id,
                    dataset_name,
                    file_path,
                    validation_timestamp,
                    total_rules,
                    passed_rules,
                    failed_rules,
                    warning_rules,
                    total_failed_records
                FROM validation_runs
                ORDER BY validation_timestamp DESC, id DESC
                """
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    def _get_database_path(self) -> Path:
        """Return the configured application database path."""
        repository_path = getattr(
            self.validation_repository,
            "database_path",
            None,
        )

        if repository_path is not None:
            return Path(repository_path)

        return DATABASE_PATH

    @staticmethod
    def _build_history_record(
        run: dict,
    ) -> LoadHistoryRecord:
        """Convert a database row into a history model."""
        validation_timestamp = _parse_timestamp(
            run["validation_timestamp"]
        )

        return LoadHistoryRecord(
            run_id=int(run["id"]),
            dataset_name=str(
                run["dataset_name"]
            ),
            file_path=str(
                run["file_path"]
            ),
            validation_timestamp=validation_timestamp,
            total_rules=int(
                run["total_rules"]
            ),
            passed_rules=int(
                run["passed_rules"]
            ),
            failed_rules=int(
                run["failed_rules"]
            ),
            warning_rules=int(
                run["warning_rules"]
            ),
            total_failed_records=int(
                run["total_failed_records"]
            ),
        )


def _parse_timestamp(value: str) -> datetime:
    """Convert an ISO timestamp into a datetime object."""
    return datetime.fromisoformat(value)
