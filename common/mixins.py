"""
Common mixins for Django REST Framework views.
"""


class LanguageSensitiveMixin:
    """
    Mixin to automatically add Vary: Accept-Language header to all responses.

    This ensures proper HTTP caching behavior for internationalized endpoints
    that may return different content based on Accept-Language header.

    Usage:
        class MyView(LanguageSensitiveMixin, APIView):
            pass

    The mixin works by overriding finalize_response to add the Vary header
    to all response types (2xx, 4xx, 5xx).
    """

    def finalize_response(self, request, response, *args, **kwargs):
        """Override finalize_response to add Vary: Accept-Language header."""
        response = super().finalize_response(request, response, *args, **kwargs)

        # Add Vary: Accept-Language header only when language resolution
        # depends on Accept-Language header (not ?lang query param)
        # This minimizes cache fragmentation for ?lang requests
        if "lang" not in request.GET:
            vary_header = response.get("Vary", "")
            if "Accept-Language" not in vary_header:
                response["Vary"] = (vary_header + ", " if vary_header else "") + "Accept-Language"

        return response
