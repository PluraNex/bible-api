"""
Middleware for Bible API.
"""
import logging
import uuid

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    Middleware to add a unique request ID to each request.

    The request ID is added to:
    - Request object (request.request_id)
    - Response headers (X-Request-ID)
    - Logging context
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Try to get existing request ID from header
        request_id = request.META.get("HTTP_X_REQUEST_ID")

        # Validate request ID format (must be valid UUID)
        if request_id:
            try:
                # Test if it's a valid UUID - use the provided one if valid
                uuid.UUID(request_id)
                # Valid UUID, use it as-is
            except ValueError:
                # Invalid format, generate new one
                request_id = str(uuid.uuid4())
        else:
            # No request ID provided, generate new one
            request_id = str(uuid.uuid4())

        request.request_id = request_id

        # Add to logging context
        with logging_context(request_id=request_id):
            response = self.get_response(request)

        # Always add to response headers (either reused or generated)
        response["X-Request-ID"] = request_id

        return response


class _LoggingContext:
    """Thread-local context for logging."""

    def __init__(self):
        self.request_id = None


_context = _LoggingContext()


class logging_context:
    """Context manager for logging context."""

    def __init__(self, request_id=None):
        self.request_id = request_id
        self.old_request_id = None

    def __enter__(self):
        self.old_request_id = getattr(_context, "request_id", None)
        _context.request_id = self.request_id
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _context.request_id = self.old_request_id
