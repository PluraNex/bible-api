"""
Tests for authentication models.
"""
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from bible.models import APIKey


class APIKeyModelTest(TestCase):
    """Tests for APIKey model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")

    def test_apikey_creation(self):
        """Test API key creation and automatic key generation."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "write"])

        self.assertEqual(api_key.name, "Test Key")
        self.assertEqual(api_key.user, self.user)
        self.assertTrue(len(api_key.key) > 20)  # Should auto-generate key
        self.assertEqual(api_key.scopes, ["read", "write"])
        self.assertEqual(api_key.rate_limit, 1000)  # Default value
        self.assertTrue(api_key.is_active)

    def test_apikey_custom_key(self):
        """Test API key creation with custom key."""
        custom_key = "custom-test-key-12345"
        api_key = APIKey.objects.create(name="Custom Key", key=custom_key, user=self.user)
        self.assertEqual(api_key.key, custom_key)

    def test_apikey_unique_key(self):
        """Test that API keys must be unique."""
        key = "duplicate-key"
        APIKey.objects.create(name="First Key", key=key, user=self.user)

        with self.assertRaises(IntegrityError):
            APIKey.objects.create(name="Second Key", key=key, user=self.user)  # Duplicate key

    def test_apikey_scope_checking(self):
        """Test scope checking functionality."""
        api_key = APIKey.objects.create(name="Scoped Key", user=self.user, scopes=["read", "write", "ai"])

        self.assertTrue(api_key.has_scope("read"))
        self.assertTrue(api_key.has_scope("write"))
        self.assertTrue(api_key.has_scope("ai"))
        self.assertFalse(api_key.has_scope("admin"))
        self.assertFalse(api_key.has_scope("audio"))

    def test_apikey_string_representation(self):
        """Test string representation shows name and key prefix."""
        api_key = APIKey.objects.create(name="Display Test", user=self.user)
        str_repr = str(api_key)
        self.assertIn("Display Test", str_repr)
        self.assertIn(api_key.key[:8], str_repr)

    def test_apikey_update_last_used(self):
        """Test updating last used timestamp."""
        api_key = APIKey.objects.create(name="Usage Test", user=self.user)

        self.assertIsNone(api_key.last_used_at)
        api_key.update_last_used()
        self.assertIsNotNone(api_key.last_used_at)
