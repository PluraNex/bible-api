"""
Standardized error handling for Bible API.
"""
import logging
import uuid
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        code: str = "api_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found", resource_type: str = "resource"):
        super().__init__(
            message=message,
            code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type},
        )


class PermissionError(APIError):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied", required_scopes: list | None = None):
        super().__init__(
            message=message,
            code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"required_scopes": required_scopes or []},
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(
            message=message,
            code="throttled",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
        )


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized error responses.
    Follows blueprint format: top-level detail, code, errors, request_id fields.
    """
    # Get request ID from context
    request = context.get("request")
    request_id = getattr(request, "request_id", str(uuid.uuid4()))

    # Handle APIError instances
    if isinstance(exc, APIError):
        error_response = {
            "detail": exc.message,
            "code": exc.code,
            "request_id": request_id,
        }

        # Add errors field if details exist
        if exc.details:
            error_response["errors"] = exc.details

        # Log error (without sensitive data)
        logger.error(
            f"API Error: {exc.code} - {exc.message}",
            extra={
                "request_id": request_id,
                "error_code": exc.code,
                "status_code": exc.status_code,
                "path": request.path if request else None,
                "method": request.method if request else None,
                "user_id": getattr(request.user, "id", None) if request and hasattr(request, "user") else None,
                "view": context.get("view").__class__.__name__ if context.get("view") else None,
            },
        )

        # Set response with appropriate headers
        response = Response(error_response, status=exc.status_code)

        # Add specific headers
        if exc.status_code == 401:
            response["WWW-Authenticate"] = 'Api-Key realm="bible-api"'
        elif exc.status_code == 429 and "retry_after" in exc.details:
            response["Retry-After"] = str(exc.details["retry_after"])

        return response

    # Handle DRF validation errors
    response = exception_handler(exc, context)
    if response is not None:
        # Standardize DRF errors to blueprint format
        error_code = "api_error"
        detail = "An error occurred"
        errors = {}

        # Handle specific HTTP errors
        if response.status_code == 404:
            error_code = "not_found"
            detail = "Resource not found"
        elif response.status_code == 401:
            error_code = "authentication_failed"
            detail = "Authentication credentials were not provided"
        elif response.status_code == 403:
            error_code = "permission_denied"
            detail = "You do not have permission to perform this action"
        elif response.status_code == 405:
            error_code = "method_not_allowed"
            detail = f"Method '{request.method}' not allowed"
        elif response.status_code == 429:
            error_code = "throttled"
            detail = "Request was throttled"
        elif response.status_code == 400:
            error_code = "validation_error"
            detail = "Invalid input"
            # Preserve DRF validation structure in errors field
            if isinstance(response.data, dict):
                errors = response.data

        standardized_response = {
            "detail": detail,
            "code": error_code,
            "request_id": request_id,
        }

        # Add errors field if we have validation errors
        if errors:
            standardized_response["errors"] = errors

        # Log error
        logger.warning(
            f"HTTP Error: {response.status_code} - {detail}",
            extra={
                "request_id": request_id,
                "error_code": error_code,
                "status_code": response.status_code,
                "path": request.path if request else None,
                "method": request.method if request else None,
                "user_id": getattr(request.user, "id", None) if request and hasattr(request, "user") else None,
                "view": context.get("view").__class__.__name__ if context.get("view") else None,
            },
        )

        # Create response with appropriate headers
        new_response = Response(standardized_response, status=response.status_code)

        # Add specific headers
        if response.status_code == 401:
            new_response["WWW-Authenticate"] = 'Api-Key realm="bible-api"'
        elif response.status_code == 429:
            # Try to get retry-after from original response headers
            retry_after = response.get("Retry-After")
            if retry_after:
                new_response["Retry-After"] = retry_after

        return new_response

    # Handle unexpected errors
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.path if request else None,
            "method": request.method if request else None,
            "user_id": getattr(request.user, "id", None) if request and hasattr(request, "user") else None,
            "view": context.get("view").__class__.__name__ if context.get("view") else None,
        },
    )

    return Response(
        {
            "detail": "An internal server error occurred",
            "code": "internal_server_error",
            "request_id": request_id,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
