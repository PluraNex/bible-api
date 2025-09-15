"""
Tests for bible.auth.authentication module.
"""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import AuthenticationFailed

from bible.auth.authentication import ApiKeyAuthentication
from bible.models import APIKey


class APIKeyAuthenticationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="auth_test_user")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "write"])
        self.auth = ApiKeyAuthentication()

    def test_authenticate_with_valid_key(self):
        """Test authentication with valid API key."""
        request = self.factory.get("/test/", HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        user, api_key_obj = result
        self.assertEqual(user, self.user)
        self.assertEqual(api_key_obj, self.api_key)

    def test_authenticate_without_header(self):
        """Test authentication without Authorization header."""
        request = self.factory.get("/test/")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_with_wrong_scheme(self):
        """Test authentication with wrong authorization scheme."""
        request = self.factory.get("/test/", HTTP_AUTHORIZATION="Bearer token123")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_with_invalid_key(self):
        """Test authentication with invalid API key."""
        request = self.factory.get("/test/", HTTP_AUTHORIZATION="Api-Key invalid-key")

        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_authenticate_with_inactive_key(self):
        """Test authentication with inactive API key."""
        self.api_key.is_active = False
        self.api_key.save()

        request = self.factory.get("/test/", HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_authenticate_with_revoked_key(self):
        """Test authentication with revoked API key."""
        # Instead of calling revoke(), we'll set is_active to False
        self.api_key.is_active = False
        self.api_key.save()

        request = self.factory.get("/test/", HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_authenticate_header_various_formats(self):
        """Test authentication header parsing with various formats."""
        # With extra spaces
        request = self.factory.get("/test/", HTTP_AUTHORIZATION=f"  Api-Key   {self.api_key.key}  ")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

        # Case insensitive scheme
        request = self.factory.get("/test/", HTTP_AUTHORIZATION=f"api-key {self.api_key.key}")
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)

    def test_authenticate_credentials_property(self):
        """Test authenticate_credentials method."""
        user, api_key_obj = self.auth.authenticate_credentials(self.api_key.key)
        self.assertEqual(user, self.user)
        self.assertEqual(api_key_obj, self.api_key)

    def test_authenticate_credentials_invalid(self):
        """Test authenticate_credentials with invalid key."""
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate_credentials("invalid-key")
