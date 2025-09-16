"""Tests for common.exceptions module."""
import pytest
from unittest.mock import Mock, patch
from rest_framework import status

from common.exceptions import (
    APIError, ValidationError, NotFoundError, PermissionError, RateLimitError,
    _request_id_from_context, _response_payload, _apply_headers,
    _STATUS_CODE_MAPPING
)


class TestAPIError:
    """Test base APIError class."""

    def test_default_initialization(self):
        """Test APIError with default values."""
        error = APIError("Something went wrong")

        assert error.message == "Something went wrong"
        assert error.code == "api_error"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details == {}
        assert str(error) == "Something went wrong"

    def test_custom_initialization(self):
        """Test APIError with custom values."""
        details = {"field": "value"}
        error = APIError(
            "Custom error",
            code="custom_code",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

        assert error.message == "Custom error"
        assert error.code == "custom_code"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.details == details


class TestValidationError:
    """Test ValidationError class."""

    def test_default_initialization(self):
        """Test ValidationError with default values."""
        error = ValidationError("Validation failed")

        assert error.message == "Validation failed"
        assert error.code == "validation_error"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details == {}

    def test_with_details(self):
        """Test ValidationError with details."""
        details = {"email": ["This field is required"]}
        error = ValidationError("Validation failed", details=details)

        assert error.details == details


class TestNotFoundError:
    """Test NotFoundError class."""

    def test_default_initialization(self):
        """Test NotFoundError with default values."""
        error = NotFoundError()

        assert error.message == "Resource not found"
        assert error.code == "not_found"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.details == {"resource_type": "resource"}

    def test_custom_initialization(self):
        """Test NotFoundError with custom values."""
        error = NotFoundError("Book not found", resource_type="book")

        assert error.message == "Book not found"
        assert error.details == {"resource_type": "book"}


class TestPermissionError:
    """Test PermissionError class."""

    def test_default_initialization(self):
        """Test PermissionError with default values."""
        error = PermissionError()

        assert error.message == "Permission denied"
        assert error.code == "permission_denied"
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.details == {"required_scopes": []}

    def test_with_scopes(self):
        """Test PermissionError with required scopes."""
        scopes = ["read", "write"]
        error = PermissionError("Need more permissions", required_scopes=scopes)

        assert error.message == "Need more permissions"
        assert error.details == {"required_scopes": scopes}


class TestRateLimitError:
    """Test RateLimitError class."""

    def test_default_initialization(self):
        """Test RateLimitError with default values."""
        error = RateLimitError()

        assert error.message == "Rate limit exceeded"
        assert error.code == "throttled"
        assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert error.details == {"retry_after": None}

    def test_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Too many requests", retry_after=60)

        assert error.message == "Too many requests"
        assert error.details == {"retry_after": 60}


class TestUtilityFunctions:
    """Test utility functions."""

    def test_request_id_from_context_with_request_id(self):
        """Test getting request_id from context when it exists."""
        mock_request = Mock()
        mock_request.request_id = "test-request-id"
        context = {"request": mock_request}

        result = _request_id_from_context(context)
        assert result == "test-request-id"

    def test_request_id_from_context_no_request(self):
        """Test getting request_id when no request in context."""
        context = {}

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "generated-uuid"
            result = _request_id_from_context(context)
            assert result == "generated-uuid"

    def test_response_payload_basic(self):
        """Test basic response payload creation."""
        payload = _response_payload("Error message", "error_code", "req-123")

        expected = {
            "detail": "Error message",
            "code": "error_code",
            "request_id": "req-123"
        }
        assert payload == expected

    def test_apply_headers_www_authenticate(self):
        """Test applying WWW-Authenticate header."""
        response = {}
        _apply_headers(response, www_auth=True)

        assert response["WWW-Authenticate"] == 'Api-Key realm="bible-api"'