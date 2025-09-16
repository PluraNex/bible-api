"""Tests for common.data_config module."""
import pytest
from pathlib import Path

from common.data_config import (
    DATA_DIR, EXTERNAL_DIR, PROCESSED_DIR, SCHEMAS_DIR,
    DEFAULT_BATCH_SIZE, MIN_VERSE_LENGTH, MAX_VERSE_LENGTH, EXPECTED_VERSE_RANGE,
    MIN_DETECTION_CONFIDENCE, HIGH_CONFIDENCE_THRESHOLD,
    DEFAULT_LICENSE_CODE, DEFAULT_LICENSE_NAME,
    CROSSREF_BATCH_SIZE, DEFAULT_CROSSREF_FILE,
    LOG_FORMAT, LOG_LEVEL,
    QUALITY_CHECKS,
    BIBLE_FILE_PATTERNS, IGNORE_PATTERNS,
    MIGRATION_TIMEOUT, POPULATION_TIMEOUT, VALIDATION_TIMEOUT
)


class TestDataConfig:
    """Test data configuration constants and structure."""

    def test_directory_structure(self):
        """Test that directory constants are properly configured."""
        assert isinstance(DATA_DIR, Path)
        assert DATA_DIR == Path("data")

        assert isinstance(EXTERNAL_DIR, Path)
        assert str(EXTERNAL_DIR) == "data/external"

        assert isinstance(PROCESSED_DIR, Path)
        assert str(PROCESSED_DIR) == "data/processed"

        assert isinstance(SCHEMAS_DIR, Path)
        assert str(SCHEMAS_DIR) == "data/schemas"

    def test_processing_settings(self):
        """Test processing configuration values."""
        assert isinstance(DEFAULT_BATCH_SIZE, int)
        assert DEFAULT_BATCH_SIZE > 0

        assert isinstance(MIN_VERSE_LENGTH, int)
        assert MIN_VERSE_LENGTH > 0

        assert isinstance(MAX_VERSE_LENGTH, int)
        assert MAX_VERSE_LENGTH > MIN_VERSE_LENGTH

        assert isinstance(EXPECTED_VERSE_RANGE, tuple)
        assert len(EXPECTED_VERSE_RANGE) == 2
        assert EXPECTED_VERSE_RANGE[0] < EXPECTED_VERSE_RANGE[1]

    def test_detection_thresholds(self):
        """Test language detection thresholds."""
        assert isinstance(MIN_DETECTION_CONFIDENCE, float)
        assert 0.0 <= MIN_DETECTION_CONFIDENCE <= 1.0

        assert isinstance(HIGH_CONFIDENCE_THRESHOLD, float)
        assert 0.0 <= HIGH_CONFIDENCE_THRESHOLD <= 1.0
        assert HIGH_CONFIDENCE_THRESHOLD >= MIN_DETECTION_CONFIDENCE

    def test_database_defaults(self):
        """Test database default values."""
        assert isinstance(DEFAULT_LICENSE_CODE, str)
        assert len(DEFAULT_LICENSE_CODE) > 0

        assert isinstance(DEFAULT_LICENSE_NAME, str)
        assert len(DEFAULT_LICENSE_NAME) > 0

    def test_crossref_settings(self):
        """Test cross reference configuration."""
        assert isinstance(CROSSREF_BATCH_SIZE, int)
        assert CROSSREF_BATCH_SIZE > 0

        assert isinstance(DEFAULT_CROSSREF_FILE, str)
        assert "cross-references" in DEFAULT_CROSSREF_FILE

    def test_logging_config(self):
        """Test logging configuration."""
        assert isinstance(LOG_FORMAT, str)
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT

        assert isinstance(LOG_LEVEL, str)
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_quality_checks_structure(self):
        """Test quality checks configuration."""
        assert isinstance(QUALITY_CHECKS, dict)

        required_keys = [
            "min_books_per_bible", "min_chapters_per_book",
            "min_verses_per_chapter", "max_verse_length",
            "expected_total_verses"
        ]

        for key in required_keys:
            assert key in QUALITY_CHECKS

        # Test specific values
        assert isinstance(QUALITY_CHECKS["expected_total_verses"], tuple)
        assert len(QUALITY_CHECKS["expected_total_verses"]) == 2

    def test_file_patterns(self):
        """Test file pattern configurations."""
        assert isinstance(BIBLE_FILE_PATTERNS, list)
        assert "*.json" in BIBLE_FILE_PATTERNS

        assert isinstance(IGNORE_PATTERNS, list)
        assert ".*" in IGNORE_PATTERNS

    def test_timeouts(self):
        """Test timeout values."""
        assert isinstance(MIGRATION_TIMEOUT, int)
        assert MIGRATION_TIMEOUT > 0

        assert isinstance(POPULATION_TIMEOUT, int)
        assert POPULATION_TIMEOUT > 0

        assert isinstance(VALIDATION_TIMEOUT, int)
        assert VALIDATION_TIMEOUT > 0

        # Logical ordering
        assert VALIDATION_TIMEOUT <= MIGRATION_TIMEOUT <= POPULATION_TIMEOUT

    def test_constants_immutability(self):
        """Test that constants have expected values."""
        # Key constants should have expected values
        assert DEFAULT_BATCH_SIZE == 1000
        assert MIN_VERSE_LENGTH == 3
        assert MAX_VERSE_LENGTH == 2000
        assert EXPECTED_VERSE_RANGE == (20000, 35000)
        assert CROSSREF_BATCH_SIZE == 1000
        assert DEFAULT_LICENSE_CODE == "PD"