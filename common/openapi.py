"""
OpenAPI schemas and examples for common components.
"""
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

# Common OpenAPI parameters
LANG_PARAMETER = OpenApiParameter(
    name="lang",
    description="Language code for localized content (e.g., 'en', 'pt', 'es'). Overrides Accept-Language header.",
    required=False,
    type=str,
    location=OpenApiParameter.QUERY,
)


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response format for all API endpoints."""

    detail = serializers.CharField(help_text="Human-readable error message describing what went wrong")
    code = serializers.CharField(help_text="Machine-readable error code for programmatic handling")
    request_id = serializers.UUIDField(help_text="Unique identifier for this request, useful for debugging and support")
    errors = serializers.JSONField(
        required=False, help_text="Additional error details, typically validation errors with field-specific messages"
    )


# Common error examples
ERROR_EXAMPLES = {
    "ValidationError": {
        "detail": "Invalid input",
        "code": "validation_error",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "errors": {"name": ["This field is required"], "email": ["Enter a valid email address"]},
    },
    "NotFoundError": {
        "detail": "Resource not found",
        "code": "not_found",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
    "AuthenticationError": {
        "detail": "Authentication credentials were not provided",
        "code": "authentication_failed",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
    "PermissionError": {
        "detail": "You do not have permission to perform this action",
        "code": "permission_denied",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
    "ThrottleError": {
        "detail": "Request was throttled",
        "code": "throttled",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
    "InternalServerError": {
        "detail": "An internal server error occurred",
        "code": "internal_server_error",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
    },
}


# Common response schemas with examples
def get_error_responses():
    """Get standardized error responses for OpenAPI documentation."""
    return {
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
        405: ErrorResponseSerializer,
        429: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    }
