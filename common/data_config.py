"""
Bible API Data Configuration

Centralized configuration for all data processing operations.
"""
from pathlib import Path

# Base directories
DATA_DIR = Path("data")
EXTERNAL_DIR = DATA_DIR / "external"
PROCESSED_DIR = DATA_DIR / "processed"
SCHEMAS_DIR = DATA_DIR / "schemas"

# Processing settings
DEFAULT_BATCH_SIZE = 1000
MIN_VERSE_LENGTH = 3
MAX_VERSE_LENGTH = 2000
EXPECTED_VERSE_RANGE = (20000, 35000)

# Language detection confidence thresholds
MIN_DETECTION_CONFIDENCE = 0.6
HIGH_CONFIDENCE_THRESHOLD = 0.8

# Database defaults
DEFAULT_LICENSE_CODE = "PD"
DEFAULT_LICENSE_NAME = "Public Domain"

# Cross reference settings
CROSSREF_BATCH_SIZE = 1000
DEFAULT_CROSSREF_FILE = "data/external/cross-references.txt"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Quality thresholds
QUALITY_CHECKS = {
    "min_books_per_bible": 60,
    "min_chapters_per_book": 1,
    "min_verses_per_chapter": 1,
    "max_verse_length": 2000,
    "expected_total_verses": (25000, 35000),
}

# Common file patterns
BIBLE_FILE_PATTERNS = ["*.json"]
IGNORE_PATTERNS = [".*", "__*", "*.tmp", "*.bak"]

# Operation timeouts (seconds)
MIGRATION_TIMEOUT = 300
POPULATION_TIMEOUT = 1800
VALIDATION_TIMEOUT = 60
