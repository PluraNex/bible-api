"""
Tests for common OpenAPI components.
"""
from django.test import TestCase
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from common.openapi import ERROR_EXAMPLES, LANG_PARAMETER, ErrorResponseSerializer, get_error_responses


class OpenAPIComponentsTest(TestCase):
    """Test OpenAPI components."""

    def test_lang_parameter(self):
        """Test LANG_PARAMETER is properly configured."""
        self.assertIsInstance(LANG_PARAMETER, OpenApiParameter)
        self.assertEqual(LANG_PARAMETER.name, "lang")
        self.assertFalse(LANG_PARAMETER.required)
        self.assertEqual(LANG_PARAMETER.type, str)
        self.assertEqual(LANG_PARAMETER.location, OpenApiParameter.QUERY)
        self.assertIn("Language code", LANG_PARAMETER.description)

    def test_error_response_serializer(self):
        """Test ErrorResponseSerializer has all required fields."""
        serializer = ErrorResponseSerializer()

        # Check that all expected fields are present
        expected_fields = ["detail", "code", "request_id", "errors"]
        for field_name in expected_fields:
            self.assertIn(field_name, serializer.fields)

        # Check field types
        self.assertIsInstance(serializer.fields["detail"], serializers.CharField)
        self.assertIsInstance(serializer.fields["code"], serializers.CharField)
        self.assertIsInstance(serializer.fields["request_id"], serializers.UUIDField)
        self.assertIsInstance(serializer.fields["errors"], serializers.JSONField)

        # Check that errors field is not required
        self.assertFalse(serializer.fields["errors"].required)

    def test_error_examples_structure(self):
        """Test ERROR_EXAMPLES has expected structure."""
        expected_examples = [
            "ValidationError",
            "NotFoundError",
            "AuthenticationError",
            "PermissionError",
            "ThrottleError",
            "InternalServerError",
        ]

        for example_name in expected_examples:
            self.assertIn(example_name, ERROR_EXAMPLES)
            example = ERROR_EXAMPLES[example_name]

            # Each example should have required fields
            self.assertIn("detail", example)
            self.assertIn("code", example)
            self.assertIn("request_id", example)

            # All should be strings except errors which is optional
            self.assertIsInstance(example["detail"], str)
            self.assertIsInstance(example["code"], str)
            self.assertIsInstance(example["request_id"], str)

    def test_error_examples_validation_error_has_errors(self):
        """Test ValidationError example includes errors field."""
        validation_error = ERROR_EXAMPLES["ValidationError"]
        self.assertIn("errors", validation_error)
        self.assertIsInstance(validation_error["errors"], dict)

    def test_get_error_responses(self):
        """Test get_error_responses returns correct response mapping."""
        responses = get_error_responses()

        expected_status_codes = [400, 401, 403, 404, 405, 429, 500]

        for status_code in expected_status_codes:
            self.assertIn(status_code, responses)
            self.assertEqual(responses[status_code], ErrorResponseSerializer)

    def test_error_response_serializer_validation(self):
        """Test ErrorResponseSerializer validates data correctly."""
        # Valid data
        valid_data = {
            "detail": "Test error",
            "code": "test_error",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
        }

        serializer = ErrorResponseSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Valid data with errors
        valid_data_with_errors = {
            "detail": "Validation failed",
            "code": "validation_error",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": {"field": ["Required"]},
        }

        serializer = ErrorResponseSerializer(data=valid_data_with_errors)
        self.assertTrue(serializer.is_valid())

        # Invalid UUID should fail validation
        invalid_data = {"detail": "Test error", "code": "test_error", "request_id": "not-a-valid-uuid"}

        serializer = ErrorResponseSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("request_id", serializer.errors)
