"""
Tests for common.exceptions module.
"""
from django.http import Http404
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError

from common.exceptions import (
    APIError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    custom_exception_handler,
)
from common.exceptions import (
    ValidationError as CustomValidationError,
)


class APIErrorTest(TestCase):
    def test_api_error_creation(self):
        """Test creating APIError with default values."""
        error = APIError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.code, "api_error")
        self.assertEqual(error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_error_with_custom_values(self):
        """Test creating APIError with custom values."""
        error = APIError("Custom error", "CUSTOM_CODE", status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(error.message, "Custom error")
        self.assertEqual(error.code, "CUSTOM_CODE")
        self.assertEqual(error.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class SpecificErrorsTest(TestCase):
    def test_validation_error(self):
        """Test CustomValidationError."""
        error = CustomValidationError("Invalid input")
        self.assertEqual(error.message, "Invalid input")
        self.assertEqual(error.code, "validation_error")
        self.assertEqual(error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")
        self.assertEqual(error.message, "Resource not found")
        self.assertEqual(error.code, "not_found")
        self.assertEqual(error.status_code, status.HTTP_404_NOT_FOUND)

    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")
        self.assertEqual(error.message, "Access denied")
        self.assertEqual(error.code, "permission_denied")
        self.assertEqual(error.status_code, status.HTTP_403_FORBIDDEN)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        self.assertEqual(error.message, "Rate limit exceeded")
        self.assertEqual(error.code, "throttled")
        self.assertEqual(error.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class CustomExceptionHandlerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/test/")

    def test_handle_api_error(self):
        """Test handling APIError."""
        error = APIError("Test error", "TEST_CODE", status.HTTP_400_BAD_REQUEST)
        response = custom_exception_handler(error, {"request": self.request})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertEqual(data["code"], "TEST_CODE")
        self.assertEqual(data["detail"], "Test error")
        self.assertIn("request_id", data)

    def test_handle_validation_error(self):
        """Test handling DRF ValidationError."""
        error = ValidationError({"field": ["This field is required"]})
        response = custom_exception_handler(error, {"request": self.request})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertEqual(data["code"], "validation_error")
        self.assertIn("field", data["errors"])

    def test_handle_not_found(self):
        """Test handling DRF NotFound."""
        error = NotFound("Not found")
        response = custom_exception_handler(error, {"request": self.request})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.data
        self.assertEqual(data["code"], "not_found")

    def test_handle_http404(self):
        """Test handling Django Http404."""
        error = Http404("Page not found")
        response = custom_exception_handler(error, {"request": self.request})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.data
        self.assertEqual(data["code"], "not_found")

    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        error = Exception("Something went wrong")
        response = custom_exception_handler(error, {"request": self.request})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.data
        self.assertEqual(data["code"], "internal_server_error")
        # Should not expose sensitive error details in production
        self.assertIn("detail", data)
