"""
Project : Data Quality Checker
Project ID : 029

Application Configuration
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

APPLICATION_NAME = "Data Quality Checker"
APPLICATION_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIRECTORY = PROJECT_ROOT / "data"
INPUT_DIRECTORY = DATA_DIRECTORY / "input"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "output"
SAMPLES_DIRECTORY = DATA_DIRECTORY / "samples"

ASSETS_DIRECTORY = PROJECT_ROOT / "assets"
DOCS_DIRECTORY = PROJECT_ROOT / "docs"
LOG_DIRECTORY = PROJECT_ROOT / "logs"
SCREENSHOTS_DIRECTORY = PROJECT_ROOT / "screenshots"
RELEASES_DIRECTORY = PROJECT_ROOT / "releases"
TESTS_DIRECTORY = PROJECT_ROOT / "tests"


# ---------------------------------------------------------------------------
# Application Data
# ---------------------------------------------------------------------------

DATABASE_DIRECTORY = DATA_DIRECTORY / "output"
DATABASE_FILENAME = "data_quality_checker.db"
DATABASE_PATH = DATABASE_DIRECTORY / DATABASE_FILENAME

EXECUTION_REPORT_FILENAME = "execution_report.txt"
EXECUTION_REPORT_PATH = LOG_DIRECTORY / EXECUTION_REPORT_FILENAME


# ---------------------------------------------------------------------------
# Supported Input Formats
# ---------------------------------------------------------------------------

SUPPORTED_INPUT_EXTENSIONS = (".csv",)


# ---------------------------------------------------------------------------
# Runtime Configuration
# ---------------------------------------------------------------------------

DEFAULT_ENCODING = "utf-8"