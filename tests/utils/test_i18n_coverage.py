"""
Tests to increase coverage for bible.utils.i18n module.
"""
from django.test import TestCase
from unittest.mock import Mock

from bible.models import Language
from bible.utils.i18n import _validate_language_code, get_language_from_context


class I18nCoverageTest(TestCase):
    """Tests to cover missing lines in i18n module."""

    def test_validate_language_code_spanish(self):
        """Test Spanish language fallback."""
        # Create Spanish language for fallback
        Language.objects.create(code="es", name="Spanish")

        result = _validate_language_code("es-ES")
        self.assertEqual(result, "es")

    def test_validate_language_code_spanish_no_fallback(self):
        """Test Spanish language fallback when no 'es' exists."""
        # Don't create Spanish language
        result = _validate_language_code("es-MX")
        self.assertIsNone(result)

    def test_get_language_from_context_none(self):
        """Test get_language_from_context with None context."""
        result = get_language_from_context(None)
        self.assertEqual(result, "en")

    def test_get_language_from_context_no_request(self):
        """Test get_language_from_context with empty context."""
        result = get_language_from_context({})
        self.assertEqual(result, "en")

    def test_get_language_from_context_no_lang_code(self):
        """Test get_language_from_context with request but no lang_code."""
        mock_request = Mock()
        delattr(mock_request, 'lang_code') if hasattr(mock_request, 'lang_code') else None

        context = {"request": mock_request}
        result = get_language_from_context(context)
        self.assertEqual(result, "en")

    def test_get_language_from_context_with_lang_code(self):
        """Test get_language_from_context with request having lang_code."""
        mock_request = Mock()
        mock_request.lang_code = "pt-BR"

        context = {"request": mock_request}
        result = get_language_from_context(context)
        self.assertEqual(result, "pt-BR")