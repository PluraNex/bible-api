"""
Tests for auth OpenAPI extension.
"""
from django.test import TestCase

from bible.auth.openapi import ApiKeyAuthenticationExtension


class ApiKeyAuthenticationExtensionTest(TestCase):
    """Test ApiKeyAuthenticationExtension."""

    def setUp(self):
        # Mock the target parameter that's required by the parent class
        self.extension = ApiKeyAuthenticationExtension(target=None)

    def test_extension_properties(self):
        """Test extension properties are correctly set."""
        self.assertEqual(self.extension.target_class, "bible.auth.authentication.ApiKeyAuthentication")
        self.assertEqual(self.extension.name, "ApiKeyAuth")
        self.assertTrue(self.extension.match_subclasses)
        self.assertEqual(self.extension.priority, -1)

    def test_get_security_definition(self):
        """Test security definition generation."""
        definition = self.extension.get_security_definition(None)

        expected = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "API Key authentication. Format: Api-Key your_api_key_here",
        }

        self.assertEqual(definition, expected)

    def test_get_security_requirement(self):
        """Test security requirement generation."""
        requirement = self.extension.get_security_requirement(None)

        expected = {"ApiKeyAuth": []}
        self.assertEqual(requirement, expected)
