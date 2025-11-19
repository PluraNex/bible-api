"""
Custom pagination classes for the Bible API.
"""

from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with consistent metadata format.

    Provides pagination with page links, count, and customizable page size.
    """

    page_size = 20
    page_size_query_param = "page_size"
    alternate_page_size_query_param = "limit"
    max_page_size = 100

    def get_page_size(self, request):
        """Allow page_size override via ?page_size= or legacy ?limit=."""
        size = super().get_page_size(request)
        if size is None and self.alternate_page_size_query_param:
            raw_value = request.query_params.get(self.alternate_page_size_query_param)
            if raw_value is not None:
                try:
                    size = _positive_int(raw_value, strict=True, cutoff=self.max_page_size)
                except (TypeError, ValueError):
                    size = self.page_size
        return size

    def get_paginated_response(self, data):
        """Return paginated response with consistent metadata format."""
        return Response(
            {
                "pagination": {
                    "count": self.page.paginator.count,
                    "num_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "results": data,
            }
        )
