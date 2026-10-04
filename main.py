"""
Project : Data Quality Checker
Project ID : 029

Application Entry Point
"""

import tkinter as tk

from src.core.profiling.profiling_engine import ProfilingEngine
from src.services.dataset_service import DatasetService
from src.services.results_repository import ResultsRepository
from src.ui.main_window import MainWindow


def create_application() -> MainWindow:
    """Create and configure the Data Quality Checker application."""
    root = tk.Tk()

    dataset_service = DatasetService()
    profiling_engine = ProfilingEngine()
    results_repository = ResultsRepository()

    return MainWindow(
        root=root,
        dataset_service=dataset_service,
        profiling_engine=profiling_engine,
        results_repository=results_repository,
    )


def main() -> None:
    """Start the Data Quality Checker application."""
    application = create_application()
    application.root.mainloop()


if __name__ == "__main__":
    main()