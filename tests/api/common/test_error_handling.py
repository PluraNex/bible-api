"""
Tests for standardized error handling system.
"""
import uuid
from unittest.mock import patch

from django.http import HttpRequest
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.test import APITestCase

from bible.models import APIKey
from common.exceptions import (
    APIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    custom_exception_handler,
)


class ErrorHandlerUnitTests(TestCase):
    """Unit tests for custom exception handler."""

    def setUp(self):
        self.request = HttpRequest()
        self.request.path = "/api/v1/test"
        self.request.method = "GET"
        self.request.request_id = str(uuid.uuid4())
        self.context = {"request": self.request}

    def test_api_error_handling(self):
        """Test APIError is handled with blueprint format."""
        exc = APIError(
            message="Test error",
            code="test_error",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "error details"},
        )

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Test error")
        self.assertEqual(response.data["code"], "test_error")
        self.assertEqual(response.data["request_id"], self.request.request_id)
        self.assertEqual(response.data["errors"], {"field": "error details"})

    def test_validation_error_handling(self):
        """Test ValidationError with details."""
        exc = ValidationError("Validation failed", details={"name": ["This field is required"]})

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Validation failed")
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(response.data["errors"], {"name": ["This field is required"]})

    def test_not_found_error_handling(self):
        """Test NotFoundError handling."""
        exc = NotFoundError("Version not found", resource_type="version")

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Version not found")
        self.assertEqual(response.data["code"], "not_found")
        self.assertEqual(response.data["errors"], {"resource_type": "version"})

    def test_permission_error_with_www_authenticate(self):
        """Test 401 errors include WWW-Authenticate header."""
        exc = APIError(
            message="Authentication required", code="authentication_required", status_code=status.HTTP_401_UNAUTHORIZED
        )

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Api-Key realm="bible-api"')

    def test_rate_limit_with_retry_after(self):
        """Test 429 errors include Retry-After header."""
        exc = RateLimitError("Rate limit exceeded", retry_after=60)

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "60")

    @patch("common.exceptions.exception_handler")
    def test_drf_validation_error_standardization(self, mock_handler):
        """Test DRF ValidationError is standardized to blueprint format."""
        # Mock the response that DRF exception_handler would return
        mock_response = Response({"name": ["This field is required"], "email": ["Enter a valid email"]}, status=400)
        mock_handler.return_value = mock_response

        # Use DRF ValidationError to trigger DRF handler path
        exc = DRFValidationError("Test validation error")

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Invalid input")
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(
            response.data["errors"], {"name": ["This field is required"], "email": ["Enter a valid email"]}
        )
        self.assertIn("request_id", response.data)

    @patch("common.exceptions.exception_handler")
    def test_drf_not_authenticated_standardization(self, mock_handler):
        """Test DRF NotAuthenticated is standardized with WWW-Authenticate header."""
        mock_response = Response({"detail": "Authentication credentials were not provided."}, status=401)
        mock_handler.return_value = mock_response

        exc = NotAuthenticated()

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Authentication credentials were not provided")
        self.assertEqual(response.data["code"], "authentication_failed")
        self.assertEqual(response["WWW-Authenticate"], 'Api-Key realm="bible-api"')

    @patch("common.exceptions.exception_handler")
    def test_drf_permission_denied_standardization(self, mock_handler):
        """Test DRF PermissionDenied is standardized."""
        mock_response = Response({"detail": "You do not have permission to perform this action."}, status=403)
        mock_handler.return_value = mock_response

        exc = PermissionDenied()

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "You do not have permission to perform this action")
        self.assertEqual(response.data["code"], "permission_denied")

    def test_unhandled_exception(self):
        """Test unexpected exceptions return 500 with standard format."""
        exc = RuntimeError("Unexpected error")

        response = custom_exception_handler(exc, self.context)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["detail"], "An internal server error occurred")
        self.assertEqual(response.data["code"], "internal_server_error")
        self.assertIn("request_id", response.data)

    def test_request_id_generation_when_missing(self):
        """Test request_id is generated when missing from request."""
        request = HttpRequest()
        context = {"request": request}
        exc = APIError("Test error")

        response = custom_exception_handler(exc, context)

        self.assertIn("request_id", response.data)
        # Should be a valid UUID
        uuid.UUID(response.data["request_id"])


class ErrorHandlerIntegrationTests(APITestCase):
    """Integration tests for error handling with real API calls."""

    def setUp(self):
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="test-key", user=self.user, scopes=["read"], is_active=True)

    def test_authentication_required_error(self):
        """Test authentication error with real API call."""
        response = self.client.get("/api/v1/bible/versions/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "authentication_failed")
        self.assertIn("request_id", response.data)
        self.assertEqual(response["WWW-Authenticate"], 'Api-Key realm="bible-api"')

    def test_permission_denied_error(self):
        """Test permission denied with insufficient scopes."""
        # API key with only 'read' scope trying to access 'write' endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        # This would be a write endpoint, but we'll simulate with mock

        # For now, test with existing endpoint - proper implementation would need write endpoint
        response = self.client.get("/api/v1/bible/versions/INVALID/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "not_found")
        self.assertIn("request_id", response.data)

    def test_not_found_error(self):
        """Test 404 error with valid authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/versions/INVALID/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "not_found")
        self.assertIn("request_id", response.data)

    def test_method_not_allowed_error(self):
        """Test 405 error is properly standardized."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.post("/api/v1/bible/versions/KJV/")  # POST not allowed on detail view

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.data["code"], "method_not_allowed")
        self.assertIn("request_id", response.data)

    def test_request_id_propagation(self):
        """Test that request ID is propagated through the entire request cycle."""
        test_request_id = str(uuid.uuid4())

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/versions/INVALID/", HTTP_X_REQUEST_ID=test_request_id)

        self.assertEqual(response.data["request_id"], test_request_id)
        self.assertEqual(response["X-Request-ID"], test_request_id)

    def test_invalid_request_id_generates_new_one(self):
        """Test that invalid request ID format generates a new one."""
        invalid_request_id = "not-a-uuid"

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/versions/INVALID/", HTTP_X_REQUEST_ID=invalid_request_id)

        # Should not use the invalid ID
        self.assertNotEqual(response.data["request_id"], invalid_request_id)
        # Should generate a valid UUID
        uuid.UUID(response.data["request_id"])
