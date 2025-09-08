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


def _request_id_from_context(context: dict) -> str:
    request = context.get("request")
    return getattr(request, "request_id", str(uuid.uuid4()))


def _log(
    level: str,
    fmt: str,
    *args,
    context: dict,
    request,
    status_code: int,
    error_code: str | None = None,
    exc_info: bool = False,
) -> None:
    meta = {
        "request_id": getattr(request, "request_id", None),
        "error_code": error_code,
        "status_code": status_code,
        "path": getattr(request, "path", None),
        "method": getattr(request, "method", None),
        "user_id": getattr(getattr(request, "user", None), "id", None),
        "view": context.get("view").__class__.__name__ if context.get("view") else None,
    }
    log = logger.error if level == "error" else logger.warning
    # Lazy logging with formatting args
    log(fmt, *args, extra=meta, exc_info=exc_info)


def _response_payload(detail: str, code: str, request_id: str, errors: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": detail, "code": code, "request_id": request_id}
    if errors:
        payload["errors"] = errors
    return payload


def _apply_headers(resp: Response, *, www_auth: bool = False, retry_after: str | None = None) -> None:
    if www_auth:
        resp["WWW-Authenticate"] = 'Api-Key realm="bible-api"'
    if retry_after:
        resp["Retry-After"] = retry_after


def _handle_api_error(exc: APIError, *, request_id: str, request, context: dict) -> Response:
    payload = _response_payload(exc.message, exc.code, request_id, errors=exc.details or None)
    _log(
        "error",
        "API Error: %s - %s",
        exc.code,
        exc.message,
        context=context,
        request=request,
        status_code=exc.status_code,
        error_code=exc.code,
    )
    resp = Response(payload, status=exc.status_code)
    www = exc.status_code == 401
    ra = (
        str(exc.details.get("retry_after"))
        if exc.status_code == 429 and exc.details and exc.details.get("retry_after") is not None
        else None
    )
    _apply_headers(resp, www_auth=www, retry_after=ra)
    return resp


# Status code to error mapping
_STATUS_CODE_MAPPING = {
    404: ("not_found", "Resource not found"),
    401: ("authentication_failed", "Authentication credentials were not provided"),
    403: ("permission_denied", "You do not have permission to perform this action"),
    405: ("method_not_allowed", "Method not allowed"),  # Will be customized below
    429: ("throttled", "Request was throttled"),
    400: ("validation_error", "Invalid input"),
}


def _map_drf_response(response: Response, request) -> tuple[str, str, dict[str, Any] | None, str | None]:
    """Return (detail, code, errors, retry_after) from DRF response."""
    status_code = response.status_code
    errors: dict[str, Any] | None = None
    retry_after: str | None = None

    if status_code in _STATUS_CODE_MAPPING:
        code, detail = _STATUS_CODE_MAPPING[status_code]

        # Handle special cases
        if status_code == 405:
            detail = f"Method '{getattr(request, 'method', 'UNKNOWN')}' not allowed"
        elif status_code == 429:
            retry_after = response.get("Retry-After")
        elif status_code == 400 and isinstance(response.data, dict):
            errors = response.data  # preserve DRF shape
    else:
        code, detail = "api_error", "An error occurred"

    return detail, code, errors, retry_after


def _handle_drf_response(response: Response, *, request_id: str, request, context: dict) -> Response:
    detail, code, errors, retry_after = _map_drf_response(response, request)
    payload = _response_payload(detail, code, request_id, errors=errors)
    _log(
        "warning",
        "HTTP Error: %s",
        response.status_code,
        context=context,
        request=request,
        status_code=response.status_code,
        error_code=code,
    )
    new_resp = Response(payload, status=response.status_code)
    _apply_headers(new_resp, www_auth=response.status_code == 401, retry_after=retry_after)
    return new_resp


def custom_exception_handler(exc, context):
    """Standardized error responses for the API."""
    request = context.get("request")
    request_id = _request_id_from_context(context)

    if isinstance(exc, APIError):
        return _handle_api_error(exc, request_id=request_id, request=request, context=context)

    drf_resp = exception_handler(exc, context)
    if drf_resp is not None:
        return _handle_drf_response(drf_resp, request_id=request_id, request=request, context=context)

    _log(
        "error",
        "Unhandled exception: %s",
        exc,
        context=context,
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        exc_info=True,
    )
    return Response(
        _response_payload("An internal server error occurred", "internal_server_error", request_id),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
