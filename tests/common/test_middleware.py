"""
Tests for common middleware.
"""
import uuid
from unittest.mock import Mock

from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from common.middleware import RequestIDMiddleware


class RequestIDMiddlewareTest(TestCase):
    """Test RequestIDMiddleware."""

    def setUp(self):
        """Set up test data."""
        self.get_response = Mock(return_value=HttpResponse())
        self.middleware = RequestIDMiddleware(self.get_response)

    def test_middleware_initialization(self):
        """Test middleware initializes correctly."""
        self.assertEqual(self.middleware.get_response, self.get_response)

    def test_generates_request_id_when_none_provided(self):
        """Test that middleware generates request ID when none provided."""
        request = HttpRequest()
        request.META = {}

        response = self.middleware(request)

        # Should generate a valid UUID
        self.assertIsNotNone(request.request_id)
        uuid.UUID(request.request_id)  # Should not raise

        # Should add to response headers
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_uses_valid_request_id_from_header(self):
        """Test that middleware uses valid request ID from header."""
        request = HttpRequest()
        valid_uuid = str(uuid.uuid4())
        request.META = {"HTTP_X_REQUEST_ID": valid_uuid}

        response = self.middleware(request)

        # Should use the provided UUID
        self.assertEqual(request.request_id, valid_uuid)
        self.assertEqual(response["X-Request-ID"], valid_uuid)

    def test_regenerates_invalid_request_id_from_header(self):
        """Test that middleware regenerates invalid request ID from header."""
        request = HttpRequest()
        invalid_uuid = "not-a-valid-uuid"
        request.META = {"HTTP_X_REQUEST_ID": invalid_uuid}

        response = self.middleware(request)

        # Should generate a new valid UUID, not use the invalid one
        self.assertNotEqual(request.request_id, invalid_uuid)
        uuid.UUID(request.request_id)  # Should not raise
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_calls_get_response(self):
        """Test that middleware calls get_response."""
        request = HttpRequest()
        request.META = {}

        self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_request_id_consistency(self):
        """Test that request ID is consistent throughout request processing."""
        request = HttpRequest()
        request.META = {}

        response = self.middleware(request)

        # Request ID should be the same in request and response
        self.assertEqual(request.request_id, response["X-Request-ID"])