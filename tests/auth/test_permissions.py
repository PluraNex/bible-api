"""
Tests for bible.auth.permissions module.
"""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from bible.auth.permissions import HasAPIScopes
from bible.models import APIKey


class HasAPIScopesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="perm_test_user")
        self.permission = HasAPIScopes()

    def test_permission_with_valid_scopes(self):
        """Test permission check with valid scopes."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "write", "ai-run"])

        request = self.factory.get("/test/")
        request.user = self.user
        request.auth = api_key  # Pass the APIKey object, not the key string

        # Mock view with required scopes
        view = type("MockView", (), {"required_scopes": ["read"]})()

        result = self.permission.has_permission(request, view)
        self.assertTrue(result)

    def test_permission_with_insufficient_scopes(self):
        """Test permission check with insufficient scopes."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        request = self.factory.post("/test/")
        request.user = self.user
        request.auth = api_key  # Pass the APIKey object, not the key string

        # Mock view requiring write scope
        view = type("MockView", (), {"required_scopes": ["write"]})()

        result = self.permission.has_permission(request, view)
        self.assertFalse(result)

    def test_permission_with_multiple_required_scopes(self):
        """Test permission check with multiple required scopes."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "ai-run"])

        request = self.factory.post("/test/")
        request.user = self.user
        request.auth = api_key  # Pass the APIKey object, not the key string

        # Mock view requiring both read and ai-run
        view = type("MockView", (), {"required_scopes": ["read", "ai-run"]})()

        result = self.permission.has_permission(request, view)
        self.assertTrue(result)

    def test_permission_with_missing_one_of_multiple_scopes(self):
        """Test permission check missing one of multiple required scopes."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        request = self.factory.post("/test/")
        request.user = self.user
        request.auth = api_key  # Pass the APIKey object, not the key string

        # Mock view requiring both read and write
        view = type("MockView", (), {"required_scopes": ["read", "write"]})()

        result = self.permission.has_permission(request, view)
        self.assertFalse(result)

    def test_permission_without_auth(self):
        """Test permission check without authentication."""
        request = self.factory.get("/test/")
        request.user = self.user
        request.auth = None

        view = type("MockView", (), {"required_scopes": ["read"]})()

        result = self.permission.has_permission(request, view)
        self.assertFalse(result)

    def test_permission_with_no_required_scopes(self):
        """Test permission check when view has no required_scopes."""
        request = self.factory.get("/test/")
        request.user = self.user
        request.auth = "some-key"

        # Mock view without required_scopes
        view = type("MockView", (), {})()

        result = self.permission.has_permission(request, view)
        self.assertTrue(result)

    def test_permission_with_wildcard_scope(self):
        """Test permission check with wildcard scope."""
        api_key = APIKey.objects.create(name="Admin Key", user=self.user, scopes=["*"])

        request = self.factory.post("/test/")
        request.user = self.user
        request.auth = api_key  # Pass the APIKey object, not the key string

        # Mock view requiring any scope
        view = type("MockView", (), {"required_scopes": ["write", "ai-run", "admin"]})()

        result = self.permission.has_permission(request, view)
        self.assertTrue(result)
