"""
Global test configuration for Bible API.
Provides common fixtures and test utilities following API_TESTING_BEST_PRACTICES.md §14.
"""
import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APIClient

from bible.models import APIKey, BookName, CanonicalBook, Language, Testament, Version

# ========================================
# Basic Fixtures
# ========================================


@pytest.fixture
def api_client():
    """Fixture providing API client for tests."""
    return APIClient()


@pytest.fixture
def user_factory():
    """Factory function for creating test users."""

    def _create_user(username="testuser", email="test@example.com", **kwargs):
        return User.objects.create_user(username=username, email=email, **kwargs)

    return _create_user


@pytest.fixture
def user(user_factory):
    """Default test user fixture."""
    return user_factory()


# ========================================
# Authentication Fixtures (§5)
# ========================================


@pytest.fixture
def api_key_factory():
    """Factory function for creating API keys with different scopes."""

    def _create_api_key(user, name="Test Key", scopes=None):
        if scopes is None:
            scopes = ["read"]
        return APIKey.objects.create(name=name, user=user, scopes=scopes)

    return _create_api_key


@pytest.fixture
def api_key_read(user, api_key_factory):
    """API key with read permissions only."""
    return api_key_factory(user, name="Read Key", scopes=["read"])


@pytest.fixture
def api_key_write(user, api_key_factory):
    """API key with read and write permissions."""
    return api_key_factory(user, name="Write Key", scopes=["read", "write"])


@pytest.fixture
def api_key_admin(user, api_key_factory):
    """API key with full admin permissions."""
    return api_key_factory(user, name="Admin Key", scopes=["read", "write", "admin"])


@pytest.fixture
def api_key_ai(user, api_key_factory):
    """API key with AI-specific permissions."""
    return api_key_factory(user, name="AI Key", scopes=["read", "ai-run", "ai-tools"])


@pytest.fixture
def api_key_audio(user, api_key_factory):
    """API key with audio-specific permissions."""
    return api_key_factory(user, name="Audio Key", scopes=["read", "audio"])


# ========================================
# Authenticated Clients
# ========================================


@pytest.fixture
def authenticated_client(api_client, api_key_read):
    """API client authenticated with read permissions."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_read.key}")
    return api_client


@pytest.fixture
def write_client(api_client, api_key_write):
    """API client authenticated with write permissions."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_write.key}")
    return api_client


@pytest.fixture
def admin_client(api_client, api_key_admin):
    """API client authenticated with admin permissions."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_admin.key}")
    return api_client


@pytest.fixture
def ai_client(api_client, api_key_ai):
    """API client authenticated with AI permissions."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key_ai.key}")
    return api_client


# ========================================
# Domain Data Factories (§14)
# ========================================


@pytest.fixture
def languages():
    """Common languages for testing - minimal and relevant data."""
    return {
        "english": Language.objects.create(code="en", name="English"),
        "portuguese": Language.objects.create(code="pt", name="Portuguese"),
        "spanish": Language.objects.create(code="es", name="Spanish"),
    }


@pytest.fixture
def testaments():
    """Common testaments for testing."""
    return {
        "old": Testament.objects.create(name="Old Testament"),
        "new": Testament.objects.create(name="New Testament"),
    }


@pytest.fixture
def canonical_books_factory(testaments, languages):
    """Factory for creating canonical books with deterministic ordering."""

    def _create_books(count=3):
        books_data = [
            ("Gen", "Genesis", 1, testaments["old"], 50),
            ("Exo", "Exodus", 2, testaments["old"], 40),
            ("John", "John", 43, testaments["new"], 21),
            ("Matt", "Matthew", 40, testaments["new"], 28),
            ("Mark", "Mark", 41, testaments["new"], 16),
        ]

        books = {}
        for _i, (osis, name, order, testament, chapters) in enumerate(books_data[:count]):
            book = CanonicalBook.objects.create(
                osis_code=osis, canonical_order=order, testament=testament, chapter_count=chapters
            )

            # Create English name
            BookName.objects.create(canonical_book=book, language=languages["english"], name=name, abbreviation=osis)

            books[osis.lower()] = book

        return books

    return _create_books


@pytest.fixture
def canonical_books(canonical_books_factory):
    """Default set of canonical books for testing."""
    return canonical_books_factory(3)


@pytest.fixture
def versions_factory(languages):
    """Factory for creating Bible versions."""

    def _create_versions():
        return {
            "kjv": Version.objects.create(name="King James Version", code="EN_KJV", language=languages["english"]),
            "nvi": Version.objects.create(
                name="Nova Versão Internacional", code="PT_NVI", language=languages["portuguese"]
            ),
        }

    return _create_versions


@pytest.fixture
def versions(versions_factory):
    """Default Bible versions for testing."""
    return versions_factory()


# ========================================
# Performance & Testing Settings
# ========================================


@pytest.fixture
def performance_settings():
    """Settings optimized for performance tests (§8)."""
    return override_settings(
        DEBUG=False,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        # Disable unnecessary middleware for performance tests
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
    )


@pytest.fixture
def cache_settings():
    """Settings for testing caching behavior (§9)."""
    return override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "TIMEOUT": 300,
                "OPTIONS": {
                    "MAX_ENTRIES": 1000,
                },
            }
        }
    )


@pytest.fixture
def throttle_settings():
    """Settings for testing throttling behavior (§5)."""
    return override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.ScopedRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "read": "100/hour",
                "write": "20/hour",
                "search": "50/hour",
                "ai-run": "10/hour",
                "audio": "30/hour",
            },
        }
    )


# ========================================
# Test Data Helpers
# ========================================


@pytest.fixture
def minimal_bible_data(canonical_books, versions):
    """Minimal Bible data for deterministic tests (§14)."""
    from bible.models import Verse

    # Create a few verses for testing
    verses = []
    book = canonical_books["john"]
    version = versions["kjv"]

    verse_texts = [
        "In the beginning was the Word, and the Word was with God, and the Word was God.",
        "The same was in the beginning with God.",
        "All things were made by him; and without him was not any thing made that was made.",
    ]

    for i, text in enumerate(verse_texts, 1):
        verse = Verse.objects.create(book=book, version=version, chapter=1, number=i, text=text)
        verses.append(verse)

    return {"books": canonical_books, "versions": versions, "verses": verses}


# ========================================
# Pytest Configuration
# ========================================


def pytest_configure(config):
    """
    Configure pytest markers following API_TESTING_BEST_PRACTICES.md §2.
    """
    # Test type markers (§2)
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "api: API integration tests")
    config.addinivalue_line("markers", "integration: Full integration tests")
    config.addinivalue_line("markers", "performance: Performance tests (§8)")
    config.addinivalue_line("markers", "slow: Slow tests (excluded from PR runs)")

    # Functional area markers
    config.addinivalue_line("markers", "auth: Authentication/authorization tests (§5)")
    config.addinivalue_line("markers", "cache: Cache-related tests (§9)")
    config.addinivalue_line("markers", "security: Security tests (§11)")
    config.addinivalue_line("markers", "throttle: Rate limiting tests (§5)")
    config.addinivalue_line("markers", "contract: OpenAPI contract tests (§4)")

    # Domain-specific markers (§10)
    config.addinivalue_line("markers", "books: Books/verses endpoint tests")
    config.addinivalue_line("markers", "crossrefs: Cross references tests")
    config.addinivalue_line("markers", "audio: Audio/TTS tests")
    config.addinivalue_line("markers", "ai: AI agents and tools tests")
    config.addinivalue_line("markers", "resources: External resources tests")


def pytest_collection_modifyitems(config, items):
    """
    Automatically add markers based on test file location and naming.
    Following organization structure from §2.
    """
    for item in items:
        # Get test file path
        test_file = str(item.fspath)

        # Add markers based on file location
        if "/api/" in test_file:
            item.add_marker(pytest.mark.api)
        if "/integration/" in test_file:
            item.add_marker(pytest.mark.integration)
        if "/performance/" in test_file:
            item.add_marker(pytest.mark.performance)
        if "/unit/" in test_file or "/models/" in test_file or "/utils/" in test_file:
            item.add_marker(pytest.mark.unit)

        # Add domain markers based on path
        if "/bible/" in test_file:
            item.add_marker(pytest.mark.books)
        if "/crossref" in test_file:
            item.add_marker(pytest.mark.crossrefs)
        if "/audio/" in test_file:
            item.add_marker(pytest.mark.audio)
        if "/ai/" in test_file:
            item.add_marker(pytest.mark.ai)
        if "/auth/" in test_file:
            item.add_marker(pytest.mark.auth)

        # Add markers based on test naming
        test_name = item.name.lower()
        if "performance" in test_name or "query_efficiency" in test_name:
            item.add_marker(pytest.mark.performance)
        if "slow" in test_name or "concurrent" in test_name:
            item.add_marker(pytest.mark.slow)
        if "cache" in test_name:
            item.add_marker(pytest.mark.cache)
        if "auth" in test_name or "permission" in test_name:
            item.add_marker(pytest.mark.auth)
        if "throttle" in test_name or "rate_limit" in test_name:
            item.add_marker(pytest.mark.throttle)
        if "contract" in test_name or "schema" in test_name:
            item.add_marker(pytest.mark.contract)


# ========================================
# pytest CLI Options
# ========================================


def pytest_addoption(parser):
    """Add custom CLI options for test execution."""
    parser.addoption(
        "--quick", action="store_true", default=False, help="Run only quick tests (exclude slow and performance tests)"
    )
    parser.addoption("--contract-only", action="store_true", default=False, help="Run only contract compliance tests")


def pytest_runtest_setup(item):
    """Skip tests based on CLI options."""
    if item.config.getoption("--quick"):
        if "slow" in [mark.name for mark in item.iter_markers()]:
            pytest.skip("Skipping slow test in quick mode")
        if "performance" in [mark.name for mark in item.iter_markers()]:
            pytest.skip("Skipping performance test in quick mode")

    if item.config.getoption("--contract-only"):
        if "contract" not in [mark.name for mark in item.iter_markers()]:
            pytest.skip("Running only contract tests")
