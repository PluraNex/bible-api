"""
Tests for common pagination classes.
"""
from unittest.mock import Mock

from django.core.paginator import Paginator
from django.test import RequestFactory, TestCase

from common.pagination import StandardResultsSetPagination


class StandardResultsSetPaginationTest(TestCase):
    """Test StandardResultsSetPagination."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.pagination = StandardResultsSetPagination()

    def test_default_settings(self):
        """Test default pagination settings."""
        self.assertEqual(self.pagination.page_size, 20)
        self.assertEqual(self.pagination.page_size_query_param, "page_size")
        self.assertEqual(self.pagination.max_page_size, 100)

    def test_get_paginated_response_first_page(self):
        """Test paginated response for first page."""
        # Create mock objects
        request = self.factory.get("/?page=1")
        self.pagination.request = request

        # Create mock paginator and page
        items = list(range(50))  # 50 items total
        paginator = Paginator(items, 20)
        page = paginator.page(1)

        self.pagination.page = page

        # Mock the methods that would normally be set by DRF
        self.pagination.get_next_link = Mock(return_value="http://example.com/?page=2")
        self.pagination.get_previous_link = Mock(return_value=None)
        self.pagination.get_page_size = Mock(return_value=20)

        # Test data
        data = items[:20]

        response = self.pagination.get_paginated_response(data)

        self.assertEqual(response.status_code, 200)

        expected_data = {
            "pagination": {
                "count": 50,
                "num_pages": 3,
                "current_page": 1,
                "page_size": 20,
                "next": "http://example.com/?page=2",
                "previous": None,
            },
            "results": data,
        }

        self.assertEqual(response.data, expected_data)

    def test_get_paginated_response_middle_page(self):
        """Test paginated response for middle page."""
        request = self.factory.get("/?page=2")
        self.pagination.request = request

        # Create mock paginator and page for page 2
        items = list(range(50))
        paginator = Paginator(items, 20)
        page = paginator.page(2)

        self.pagination.page = page

        # Mock the methods
        self.pagination.get_next_link = Mock(return_value="http://example.com/?page=3")
        self.pagination.get_previous_link = Mock(return_value="http://example.com/?page=1")
        self.pagination.get_page_size = Mock(return_value=20)

        # Test data (second page)
        data = items[20:40]

        response = self.pagination.get_paginated_response(data)

        expected_data = {
            "pagination": {
                "count": 50,
                "num_pages": 3,
                "current_page": 2,
                "page_size": 20,
                "next": "http://example.com/?page=3",
                "previous": "http://example.com/?page=1",
            },
            "results": data,
        }

        self.assertEqual(response.data, expected_data)

    def test_get_paginated_response_last_page(self):
        """Test paginated response for last page."""
        request = self.factory.get("/?page=3")
        self.pagination.request = request

        # Create mock paginator and page for last page
        items = list(range(50))
        paginator = Paginator(items, 20)
        page = paginator.page(3)

        self.pagination.page = page

        # Mock the methods
        self.pagination.get_next_link = Mock(return_value=None)
        self.pagination.get_previous_link = Mock(return_value="http://example.com/?page=2")
        self.pagination.get_page_size = Mock(return_value=20)

        # Test data (last page - only 10 items)
        data = items[40:50]

        response = self.pagination.get_paginated_response(data)

        expected_data = {
            "pagination": {
                "count": 50,
                "num_pages": 3,
                "current_page": 3,
                "page_size": 20,
                "next": None,
                "previous": "http://example.com/?page=2",
            },
            "results": data,
        }

        self.assertEqual(response.data, expected_data)