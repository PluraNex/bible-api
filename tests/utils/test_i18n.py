"""
Tests for i18n utilities.
Tests language resolution, Accept-Language parsing, and middleware.
"""
from unittest.mock import Mock

import pytest
from django.test import RequestFactory, TestCase

from bible.models import Language
from bible.utils.i18n import (
    LanguageMiddleware,
    _parse_accept_language,
    _validate_language_code,
    mark_response_language_sensitive,
    resolve_language,
)


@pytest.mark.utils
class LanguageResolverTest(TestCase):
    """Test language resolution functionality."""

    def setUp(self):
        self.factory = RequestFactory()

        # Create test languages
        Language.objects.create(name="English", code="en")
        Language.objects.create(name="Portuguese", code="pt")
        Language.objects.create(name="Spanish", code="es")

    def test_resolve_language_from_query_param(self):
        """Test language resolution from ?lang= parameter (highest priority)."""
        request = self.factory.get("/?lang=pt")

        result = resolve_language(request)

        self.assertEqual(result, "pt")

    def test_resolve_language_from_accept_header(self):
        """Test language resolution from Accept-Language header."""
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9,en;q=0.8")

        result = resolve_language(request)

        self.assertEqual(result, "pt")

    def test_resolve_language_query_param_overrides_header(self):
        """Test that ?lang= parameter takes precedence over Accept-Language."""
        request = self.factory.get("/?lang=en", HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9")

        result = resolve_language(request)

        self.assertEqual(result, "en")

    def test_resolve_language_invalid_param_falls_back_to_header(self):
        """Test fallback to Accept-Language when ?lang= is invalid."""
        request = self.factory.get("/?lang=invalid", HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9,en;q=0.8")

        result = resolve_language(request)

        self.assertEqual(result, "pt")

    def test_resolve_language_default_fallback(self):
        """Test fallback to default when no valid language found."""
        request = self.factory.get("/")  # No lang param, no Accept-Language

        result = resolve_language(request)

        self.assertEqual(result, "en")

    def test_resolve_language_case_insensitive(self):
        """Test that language resolution is case-insensitive."""
        request = self.factory.get("/?lang=PT")

        result = resolve_language(request)

        self.assertEqual(result, "pt")

    def test_resolve_language_portuguese_variant_fallback(self):
        """Test pt-BR → pt fallback."""
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="pt-BR")

        result = resolve_language(request)

        self.assertEqual(result, "pt")


@pytest.mark.utils
class ValidateLanguageCodeTest(TestCase):
    """Test language code validation."""

    def setUp(self):
        Language.objects.create(name="English", code="en")
        Language.objects.create(name="Portuguese", code="pt")

    def test_validate_exact_match(self):
        """Test validation with exact language code match."""
        result = _validate_language_code("pt")
        self.assertEqual(result, "pt")

    def test_validate_case_normalization(self):
        """Test validation normalizes case."""
        result = _validate_language_code("PT")
        self.assertEqual(result, "pt")

    def test_validate_portuguese_variant_fallback(self):
        """Test pt-BR falls back to pt."""
        result = _validate_language_code("pt-BR")
        self.assertEqual(result, "pt")

    def test_validate_english_variant_fallback(self):
        """Test en-US falls back to en."""
        result = _validate_language_code("en-US")
        self.assertEqual(result, "en")

    def test_validate_invalid_code_returns_none(self):
        """Test invalid language code returns None."""
        result = _validate_language_code("invalid")
        self.assertIsNone(result)

    def test_validate_empty_code_returns_none(self):
        """Test empty/None language code returns None."""
        self.assertIsNone(_validate_language_code(""))
        self.assertIsNone(_validate_language_code(None))

    def test_validate_final_fallback_to_en(self):
        """Test final fallback to 'en' for unknown language."""
        result = _validate_language_code("unknown-lang")
        # _validate_language_code returns None for unknown codes
        # The final fallback to 'en' happens in resolve_language()
        self.assertIsNone(result)


@pytest.mark.utils
class ParseAcceptLanguageTest(TestCase):
    """Test Accept-Language header parsing."""

    def test_parse_simple_language(self):
        """Test parsing simple language without quality."""
        result = _parse_accept_language("en")
        self.assertEqual(result, [("en", 1.0)])

    def test_parse_multiple_languages_with_quality(self):
        """Test parsing multiple languages with quality scores."""
        result = _parse_accept_language("pt-BR,pt;q=0.9,en;q=0.8")
        expected = [("pt-br", 1.0), ("pt", 0.9), ("en", 0.8)]
        self.assertEqual(result, expected)

    def test_parse_sorted_by_quality_desc(self):
        """Test languages are sorted by quality (highest first)."""
        result = _parse_accept_language("en;q=0.5,pt;q=0.9,es;q=1.0")
        expected = [("es", 1.0), ("pt", 0.9), ("en", 0.5)]
        self.assertEqual(result, expected)

    def test_parse_invalid_quality_defaults_to_1(self):
        """Test invalid quality score defaults to 1.0."""
        result = _parse_accept_language("pt;q=invalid,en")
        expected = [("pt", 1.0), ("en", 1.0)]
        self.assertEqual(result, expected)

    def test_parse_empty_string(self):
        """Test parsing empty Accept-Language string."""
        result = _parse_accept_language("")
        self.assertEqual(result, [])

    def test_parse_with_spaces(self):
        """Test parsing with extra spaces."""
        result = _parse_accept_language("  pt-BR , pt ; q = 0.9 , en ; q = 0.8  ")
        expected = [("pt-br", 1.0), ("pt", 0.9), ("en", 0.8)]
        self.assertEqual(result, expected)


@pytest.mark.utils
class LanguageMiddlewareTest(TestCase):
    """Test language middleware functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        Language.objects.create(name="English", code="en")
        Language.objects.create(name="Portuguese", code="pt")

        # Mock response
        def mock_get_response(request):
            response = Mock()
            response.get.return_value = ""
            response.__setitem__ = Mock()
            return response

        self.middleware = LanguageMiddleware(mock_get_response)

    def test_middleware_attaches_lang_code(self):
        """Test middleware attaches lang_code to request."""
        request = self.factory.get("/?lang=pt")

        self.middleware(request)

        self.assertEqual(request.lang_code, "pt")

    def test_middleware_adds_vary_header_when_marked(self):
        """Test middleware adds Vary header for language-sensitive responses."""
        request = self.factory.get("/?lang=pt")
        request._language_sensitive = True

        response = self.middleware(request)

        response.__setitem__.assert_called_with("Vary", "Accept-Language")

    def test_middleware_appends_to_existing_vary_header(self):
        """Test middleware appends to existing Vary header."""
        request = self.factory.get("/?lang=pt")
        request._language_sensitive = True

        def mock_get_response(request):
            response = Mock()
            response.get.return_value = "Origin"
            response.__setitem__ = Mock()
            return response

        middleware = LanguageMiddleware(mock_get_response)
        response = middleware(request)

        response.__setitem__.assert_called_with("Vary", "Origin, Accept-Language")

    def test_mark_response_language_sensitive(self):
        """Test mark_response_language_sensitive function."""
        request = self.factory.get("/")

        mark_response_language_sensitive(request)

        self.assertTrue(hasattr(request, "_language_sensitive"))
        self.assertTrue(request._language_sensitive)


@pytest.mark.utils
class IntegrationTest(TestCase):
    """Integration tests for complete i18n flow."""

    def setUp(self):
        self.factory = RequestFactory()
        Language.objects.create(name="English", code="en")
        Language.objects.create(name="Portuguese", code="pt")

    def test_complete_flow_query_param(self):
        """Test complete flow with query parameter."""
        request = self.factory.get("/?lang=pt")

        # Resolve language
        lang_code = resolve_language(request)
        self.assertEqual(lang_code, "pt")

        # Mark as language sensitive
        mark_response_language_sensitive(request)
        self.assertTrue(request._language_sensitive)

    def test_complete_flow_accept_header(self):
        """Test complete flow with Accept-Language header."""
        request = self.factory.get("/", HTTP_ACCEPT_LANGUAGE="pt-BR,en;q=0.8")

        lang_code = resolve_language(request)
        self.assertEqual(lang_code, "pt")

    def test_complete_flow_fallback_chain(self):
        """Test complete fallback chain: invalid param → header → default."""
        request = self.factory.get("/?lang=invalid", HTTP_ACCEPT_LANGUAGE="fr-FR,de;q=0.8")  # Non-existent languages

        lang_code = resolve_language(request)
        self.assertEqual(lang_code, "en")  # Final fallback
