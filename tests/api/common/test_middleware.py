"""
Tests for Request ID middleware.
"""
import uuid
from unittest.mock import Mock

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from common.middleware import RequestIDMiddleware


class RequestIDMiddlewareTests(TestCase):
    """Tests for RequestIDMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK"))
        self.middleware = RequestIDMiddleware(self.get_response)

    def test_generates_request_id_when_missing(self):
        """Test that middleware generates request ID when not provided."""
        request = self.factory.get("/test/")

        response = self.middleware(request)

        # Should have request_id attribute
        self.assertTrue(hasattr(request, "request_id"))
        # Should be a valid UUID
        uuid.UUID(request.request_id)
        # Should be in response header
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_accepts_valid_request_id_from_header(self):
        """Test that middleware accepts valid UUID from X-Request-ID header."""
        test_uuid = str(uuid.uuid4())
        request = self.factory.get("/test/", HTTP_X_REQUEST_ID=test_uuid)

        response = self.middleware(request)

        # Should use the provided UUID
        self.assertEqual(request.request_id, test_uuid)
        self.assertEqual(response["X-Request-ID"], test_uuid)

    def test_rejects_invalid_request_id_format(self):
        """Test that middleware rejects invalid UUID format and generates new one."""
        invalid_uuid = "not-a-valid-uuid"
        request = self.factory.get("/test/", HTTP_X_REQUEST_ID=invalid_uuid)

        response = self.middleware(request)

        # Should not use invalid UUID
        self.assertNotEqual(request.request_id, invalid_uuid)
        # Should generate valid UUID
        uuid.UUID(request.request_id)
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_handles_empty_request_id_header(self):
        """Test that middleware handles empty request ID header."""
        request = self.factory.get("/test/", HTTP_X_REQUEST_ID="")

        response = self.middleware(request)

        # Should generate new UUID when empty
        self.assertTrue(hasattr(request, "request_id"))
        uuid.UUID(request.request_id)
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_handles_partial_uuid(self):
        """Test that middleware handles partial/malformed UUIDs."""
        partial_uuid = "550e8400-e29b-41d4"  # Missing parts
        request = self.factory.get("/test/", HTTP_X_REQUEST_ID=partial_uuid)

        response = self.middleware(request)

        # Should reject partial UUID and generate new one
        self.assertNotEqual(request.request_id, partial_uuid)
        uuid.UUID(request.request_id)
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_preserves_response_from_view(self):
        """Test that middleware preserves response from view."""
        test_response = HttpResponse("Custom response", status=201)
        get_response = Mock(return_value=test_response)
        middleware = RequestIDMiddleware(get_response)

        request = self.factory.get("/test/")
        response = middleware(request)

        # Should preserve status and content
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, b"Custom response")
        # But should add request ID header
        self.assertIn("X-Request-ID", response)
