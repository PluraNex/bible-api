"""
Middleware for Bible API.
"""

import uuid

from .logging import clear_request_context, set_request_context


class RequestIDMiddleware:
    """
    Middleware to add a unique request ID to each request.

    The request ID is added to:
    - Request object (request.request_id)
    - Response headers (X-Request-ID)
    - Logging context via contextvars (available in all downstream logs)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Try to get existing request ID from header
        request_id = request.META.get("HTTP_X_REQUEST_ID")

        # Validate request ID format (must be valid UUID)
        if request_id:
            try:
                uuid.UUID(request_id)
            except ValueError:
                request_id = str(uuid.uuid4())
        else:
            request_id = str(uuid.uuid4())

        request.request_id = request_id

        # Propagate context to all downstream loggers
        user_id = getattr(getattr(request, "user", None), "id", None)
        set_request_context(request_id, user_id=user_id, path=request.path)

        response = self.get_response(request)

        # Always add to response headers
        response["X-Request-ID"] = request_id

        clear_request_context()
        return response
