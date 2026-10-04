"""
Project : Data Quality Checker
Project ID : 029

Main Application Window
"""

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from src.config import (
    EXECUTION_REPORT_PATH,
    INPUT_DIRECTORY,
    SAMPLES_DIRECTORY,
)
from src.core.profiling.profiling_engine import ProfilingEngine
from src.models.validation_model import ValidationSummary
from src.services.dataset_service import DatasetService
from src.services.results_repository import ResultsRepository
from src.services.rule_config_service import RuleConfigService
from src.services.validation_repository import ValidationRepository
from src.services.validation_service import ValidationService


class MainWindow:
    """Main Tkinter application window."""

    def __init__(
        self,
        root: tk.Tk,
        dataset_service: DatasetService,
        profiling_engine: ProfilingEngine,
        results_repository: ResultsRepository,
        validation_service: ValidationService | None = None,
    ):
        self.root = root
        self.dataset_service = dataset_service
        self.profiling_engine = profiling_engine
        self.results_repository = results_repository

        self.validation_service = (
            validation_service
            if validation_service is not None
            else self._create_validation_service()
        )

        self.current_dataframe: pd.DataFrame | None = None
        self.current_file_path: Path | None = None
        self.current_profile = None
        self.current_validation_summary: ValidationSummary | None = None

        self.root.title("Data Quality Checker - v1.0.0")
        self.root.geometry("1200x760")
        self.root.minsize(1000, 650)

        self._build_interface()

    def _create_validation_service(self) -> ValidationService:
        """Create the validation service and its dependencies."""
        rule_config_service = RuleConfigService()
        validation_repository = ValidationRepository()

        return ValidationService(
            rule_config_service=rule_config_service,
            validation_repository=validation_repository,
            results_repository=self.results_repository,
        )

    def _build_interface(self) -> None:
        """Build the main application interface."""
        self._build_dataset_section()
        self._build_summary_section()
        self._build_results_section()
        self._build_validation_section()
        self._build_status_section()

    def _build_dataset_section(self) -> None:
        """Build dataset selection and action controls."""
        dataset_frame = ttk.LabelFrame(
            self.root,
            text="Dataset",
            padding=10,
        )
        dataset_frame.pack(
            fill="x",
            padx=10,
            pady=(10, 5),
        )

        self.file_path_var = tk.StringVar()

        ttk.Label(
            dataset_frame,
            text="CSV File:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )

        ttk.Entry(
            dataset_frame,
            textvariable=self.file_path_var,
            state="readonly",
            width=90,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
        )

        ttk.Button(
            dataset_frame,
            text="Browse",
            command=self._browse_dataset,
        ).grid(
            row=0,
            column=2,
            padx=(8, 0),
        )

        ttk.Button(
            dataset_frame,
            text="Load Dataset",
            command=self._load_dataset,
        ).grid(
            row=0,
            column=3,
            padx=(8, 0),
        )

        self.profile_button = ttk.Button(
            dataset_frame,
            text="Profile Dataset",
            command=self._profile_dataset,
            state="disabled",
        )
        self.profile_button.grid(
            row=0,
            column=4,
            padx=(8, 0),
        )

        self.validate_button = ttk.Button(
            dataset_frame,
            text="Run Validation",
            command=self._validate_dataset,
            state="disabled",
        )
        self.validate_button.grid(
            row=0,
            column=5,
            padx=(8, 0),
        )

        dataset_frame.columnconfigure(1, weight=1)

    def _build_summary_section(self) -> None:
        """Build the dataset summary section."""
        summary_frame = ttk.LabelFrame(
            self.root,
            text="Dataset Summary",
            padding=10,
        )
        summary_frame.pack(
            fill="x",
            padx=10,
            pady=5,
        )

        self.summary_var = tk.StringVar(
            value="No dataset loaded."
        )

        ttk.Label(
            summary_frame,
            textvariable=self.summary_var,
            anchor="w",
        ).pack(
            fill="x",
        )

    def _build_results_section(self) -> None:
        """Build the profiling results section."""
        profile_frame = ttk.LabelFrame(
            self.root,
            text="Column Profile",
            padding=8,
        )
        profile_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5,
        )

        columns = (
            "column",
            "type",
            "nulls",
            "null_pct",
            "unique",
            "unique_pct",
            "minimum",
            "maximum",
            "mean",
            "median",
        )

        self.profile_tree = ttk.Treeview(
            profile_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        headings = {
            "column": "Column",
            "type": "Data Type",
            "nulls": "Nulls",
            "null_pct": "Null %",
            "unique": "Unique",
            "unique_pct": "Unique %",
            "minimum": "Minimum",
            "maximum": "Maximum",
            "mean": "Mean",
            "median": "Median",
        }

        widths = {
            "column": 150,
            "type": 100,
            "nulls": 70,
            "null_pct": 80,
            "unique": 80,
            "unique_pct": 80,
            "minimum": 100,
            "maximum": 100,
            "mean": 100,
            "median": 100,
        }

        for column in columns:
            self.profile_tree.heading(
                column,
                text=headings[column],
            )
            self.profile_tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        profile_scrollbar = ttk.Scrollbar(
            profile_frame,
            orient="vertical",
            command=self.profile_tree.yview,
        )

        self.profile_tree.configure(
            yscrollcommand=profile_scrollbar.set,
        )

        self.profile_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        profile_scrollbar.pack(
            side="right",
            fill="y",
        )

    def _build_validation_section(self) -> None:
        """Build validation result and failed-record displays."""
        validation_frame = ttk.LabelFrame(
            self.root,
            text="Validation Results",
            padding=8,
        )
        validation_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5,
        )

        result_frame = ttk.Frame(validation_frame)
        result_frame.pack(
            fill="both",
            expand=True,
        )

        result_columns = (
            "rule_id",
            "column",
            "type",
            "status",
            "total",
            "failed",
            "failure_pct",
            "message",
        )

        self.validation_tree = ttk.Treeview(
            result_frame,
            columns=result_columns,
            show="headings",
            height=8,
        )

        result_headings = {
            "rule_id": "Rule ID",
            "column": "Column",
            "type": "Rule Type",
            "status": "Status",
            "total": "Total",
            "failed": "Failed",
            "failure_pct": "Failure %",
            "message": "Message",
        }

        result_widths = {
            "rule_id": 90,
            "column": 120,
            "type": 110,
            "status": 80,
            "total": 70,
            "failed": 70,
            "failure_pct": 85,
            "message": 400,
        }

        for column in result_columns:
            self.validation_tree.heading(
                column,
                text=result_headings[column],
            )
            self.validation_tree.column(
                column,
                width=result_widths[column],
                anchor="center",
            )

        validation_scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.validation_tree.yview,
        )

        self.validation_tree.configure(
            yscrollcommand=validation_scrollbar.set,
        )

        self.validation_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        validation_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.validation_tree.bind(
            "<<TreeviewSelect>>",
            self._display_failed_records,
        )

        failed_frame = ttk.LabelFrame(
            validation_frame,
            text="Failed Records",
            padding=5,
        )
        failed_frame.pack(
            fill="both",
            expand=True,
            pady=(8, 0),
        )

        failed_columns = (
            "row",
            "column",
            "rule_id",
            "actual",
            "expected",
            "message",
        )

        self.failed_tree = ttk.Treeview(
            failed_frame,
            columns=failed_columns,
            show="headings",
            height=6,
        )

        failed_headings = {
            "row": "Row",
            "column": "Column",
            "rule_id": "Rule ID",
            "actual": "Actual Value",
            "expected": "Expected",
            "message": "Message",
        }

        failed_widths = {
            "row": 60,
            "column": 120,
            "rule_id": 90,
            "actual": 180,
            "expected": 180,
            "message": 350,
        }

        for column in failed_columns:
            self.failed_tree.heading(
                column,
                text=failed_headings[column],
            )
            self.failed_tree.column(
                column,
                width=failed_widths[column],
                anchor="center",
            )

        failed_scrollbar = ttk.Scrollbar(
            failed_frame,
            orient="vertical",
            command=self.failed_tree.yview,
        )

        self.failed_tree.configure(
            yscrollcommand=failed_scrollbar.set,
        )

        self.failed_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        failed_scrollbar.pack(
            side="right",
            fill="y",
        )

    def _build_status_section(self) -> None:
        """Build the application status bar."""
        status_frame = ttk.Frame(
            self.root,
            padding=(10, 5),
        )
        status_frame.pack(
            fill="x",
            side="bottom",
        )

        self.status_var = tk.StringVar(
            value="Ready."
        )

        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
        ).pack(
            fill="x",
        )

    def _browse_dataset(self) -> None:
        """Allow the user to select a CSV dataset."""
        initial_directory = (
            str(INPUT_DIRECTORY)
            if INPUT_DIRECTORY.exists()
            else str(Path.cwd())
        )

        file_path = filedialog.askopenfilename(
            title="Select Dataset",
            initialdir=initial_directory,
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        self.file_path_var.set(file_path)
        self._set_status(
            f"Dataset selected: {Path(file_path).name}"
        )

    def _load_dataset(self) -> None:
        """Load the selected CSV dataset."""
        file_path_text = self.file_path_var.get().strip()

        if not file_path_text:
            messagebox.showwarning(
                "Dataset Required",
                "Please select a CSV dataset first.",
            )
            return

        try:
            file_path = Path(file_path_text)

            dataframe = self.dataset_service.load_csv(
                file_path
            )

            self.current_dataframe = dataframe
            self.current_file_path = file_path
            self.current_profile = None
            self.current_validation_summary = None

            self._clear_profile_results()
            self._clear_validation_results()

            row_count, column_count = (
                self.dataset_service.get_dataset_metadata(
                    dataframe
                )
            )

            self.summary_var.set(
                f"Dataset: {file_path.name}    |    "
                f"Rows: {row_count:,}    |    "
                f"Columns: {column_count}"
            )

            self.profile_button.configure(
                state="normal"
            )

            self.validate_button.configure(
                state="normal"
            )

            self._set_status(
                f"Loaded {file_path.name} successfully."
            )

            self._write_execution_checkpoint(
                "Dataset loaded",
                "PASS",
                (
                    f"{file_path.name} | "
                    f"{row_count:,} rows | "
                    f"{column_count} columns"
                ),
            )

        except Exception as error:
            self._set_status(
                "Dataset loading failed."
            )

            self._write_execution_checkpoint(
                "Dataset load",
                "FAIL",
                str(error),
            )

            messagebox.showerror(
                "Dataset Load Error",
                str(error),
            )

    def _profile_dataset(self) -> None:
        """Profile the currently loaded dataset."""
        if self.current_dataframe is None:
            messagebox.showwarning(
                "Dataset Required",
                "Load a dataset before profiling.",
            )
            return

        if self.current_file_path is None:
            return

        try:
            profile = self.profiling_engine.profile_dataset(
                dataframe=self.current_dataframe,
                dataset_name=self.current_file_path.name,
                file_path=str(self.current_file_path),
            )

            self.results_repository.save_profile(
                profile
            )

            self.current_profile = profile

            self._display_profile(profile)

            self._set_status(
                "Dataset profiling completed successfully."
            )

            self._write_execution_checkpoint(
                "Dataset profiling",
                "PASS",
                (
                    f"Duplicate rows: "
                    f"{profile.duplicate_row_count}"
                ),
            )

        except Exception as error:
            self._set_status(
                "Dataset profiling failed."
            )

            self._write_execution_checkpoint(
                "Dataset profiling",
                "FAIL",
                str(error),
            )

            messagebox.showerror(
                "Profiling Error",
                str(error),
            )

    def _validate_dataset(self) -> None:
        """Run all configured validation rules."""
        if self.current_dataframe is None:
            messagebox.showwarning(
                "Dataset Required",
                "Load a dataset before validation.",
            )
            return

        if self.current_file_path is None:
            return

        configuration_path = (
            SAMPLES_DIRECTORY / "validation_config.json"
        )

        if not configuration_path.exists():
            messagebox.showerror(
                "Validation Configuration",
                (
                    "Validation configuration was not found:\n\n"
                    f"{configuration_path}"
                ),
            )
            return

        try:
            self._set_status(
                "Running data quality validation..."
            )

            summary = self.validation_service.validate_dataset(
                dataframe=self.current_dataframe,
                dataset_name=self.current_file_path.name,
                file_path=self.current_file_path,
                configuration_path=configuration_path,
            )

            self.current_validation_summary = summary

            self._display_validation_summary(
                summary
            )

            self._set_status(
                "Data quality validation completed successfully."
            )

            self._write_execution_checkpoint(
                "Data validation",
                "PASS",
                (
                    f"Rules: {summary.total_rules} | "
                    f"Passed: {summary.passed_rules} | "
                    f"Failed: {summary.failed_rules} | "
                    f"Warnings: {summary.warning_rules} | "
                    f"Failed records: "
                    f"{summary.total_failed_records}"
                ),
            )

        except Exception as error:
            self._set_status(
                "Data quality validation failed."
            )

            self._write_execution_checkpoint(
                "Data validation",
                "FAIL",
                str(error),
            )

            messagebox.showerror(
                "Validation Error",
                str(error),
            )

    def _display_profile(self, profile) -> None:
        """Display the dataset profile."""
        self._clear_profile_results()

        for column_profile in profile.columns:
            self.profile_tree.insert(
                "",
                "end",
                values=(
                    column_profile.column_name,
                    column_profile.data_type,
                    column_profile.null_count,
                    f"{column_profile.null_percentage:.2f}",
                    column_profile.unique_count,
                    f"{column_profile.unique_percentage:.2f}",
                    self._format_value(
                        column_profile.minimum
                    ),
                    self._format_value(
                        column_profile.maximum
                    ),
                    self._format_value(
                        column_profile.mean
                    ),
                    self._format_value(
                        column_profile.median
                    ),
                ),
            )

    def _display_validation_summary(
        self,
        summary: ValidationSummary,
    ) -> None:
        """Display validation results in the UI."""
        self._clear_validation_results()

        for result in summary.results:
            item_id = self.validation_tree.insert(
                "",
                "end",
                values=(
                    result.rule_id,
                    result.column_name,
                    result.rule_type,
                    result.status,
                    result.total_records,
                    result.failed_records,
                    f"{result.failure_percentage:.2f}",
                    result.message,
                ),
            )

            self.validation_tree.item(
                item_id,
                tags=(result.status,),
            )

        self.validation_tree.tag_configure(
            "PASS",
            foreground="green",
        )

        self.validation_tree.tag_configure(
            "WARNING",
            foreground="orange",
        )

        self.validation_tree.tag_configure(
            "FAIL",
            foreground="red",
        )

        self.summary_var.set(
            f"Dataset: {summary.dataset_name}    |    "
            f"Rules: {summary.total_rules}    |    "
            f"PASS: {summary.passed_rules}    |    "
            f"FAIL: {summary.failed_rules}    |    "
            f"WARNING: {summary.warning_rules}    |    "
            f"Failed Records: {summary.total_failed_records}"
        )

    def _display_failed_records(self, event=None) -> None:
        """Display failed records for the selected validation rule."""
        self._clear_failed_records()

        if self.current_validation_summary is None:
            return

        selection = self.validation_tree.selection()

        if not selection:
            return

        selected_item = selection[0]
        values = self.validation_tree.item(
            selected_item,
            "values",
        )

        if not values:
            return

        rule_id = values[0]

        selected_result = next(
            (
                result
                for result
                in self.current_validation_summary.results
                if result.rule_id == rule_id
            ),
            None,
        )

        if selected_result is None:
            return

        for failed_record in (
            selected_result.failed_record_details
        ):
            self.failed_tree.insert(
                "",
                "end",
                values=(
                    failed_record.row_number,
                    failed_record.column_name,
                    failed_record.rule_id,
                    self._format_value(
                        failed_record.actual_value
                    ),
                    self._format_value(
                        failed_record.expected_value
                    ),
                    failed_record.message,
                ),
            )

    def _clear_profile_results(self) -> None:
        """Remove all profiling results from the UI."""
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)

    def _clear_validation_results(self) -> None:
        """Remove all validation results from the UI."""
        for item in self.validation_tree.get_children():
            self.validation_tree.delete(item)

        self._clear_failed_records()

    def _clear_failed_records(self) -> None:
        """Remove all failed-record results from the UI."""
        for item in self.failed_tree.get_children():
            self.failed_tree.delete(item)

    def _set_status(self, message: str) -> None:
        """Update the application status message."""
        self.status_var.set(message)

    def _write_execution_checkpoint(
        self,
        checkpoint: str,
        status: str,
        details: str,
    ) -> None:
        """Write a runtime checkpoint to the execution report."""
        try:
            EXECUTION_REPORT_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            timestamp = datetime.now().isoformat(
                timespec="seconds"
            )

            with EXECUTION_REPORT_PATH.open(
                "a",
                encoding="utf-8",
            ) as report:
                report.write(
                    f"{timestamp} | "
                    f"{checkpoint} | "
                    f"{status} | "
                    f"{details}\n"
                )

        except OSError:
            # Runtime reporting must not prevent the application
            # from continuing its primary operation.
            pass

    @staticmethod
    def _format_value(value) -> str:
        """Convert displayed values into readable text."""
        if value is None:
            return ""

        if isinstance(value, float):
            return f"{value:.4f}"

        return str(value)