"""
Tests for common mixins.
"""
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.mixins import LanguageSensitiveMixin


class TestLanguageSensitiveMixin(TestCase):
    """Test cases for LanguageSensitiveMixin."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

        # Create test view class that uses the mixin
        class TestView(LanguageSensitiveMixin, APIView):
            authentication_classes = []  # Disable authentication for test
            permission_classes = []  # Disable permissions for test

            def get(self, request):
                return Response({"test": "data"})

            def post(self, request):
                return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

        self.view_class = TestView

    def test_adds_vary_header_to_successful_response(self):
        """Test that mixin adds Vary: Accept-Language to 200 responses."""
        request = self.factory.get("/test/")
        view = self.view_class.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Accept-Language", response.get("Vary", ""))

    def test_adds_vary_header_to_error_response(self):
        """Test that mixin adds Vary: Accept-Language to error responses."""
        request = self.factory.post("/test/")
        view = self.view_class.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Accept-Language", response.get("Vary", ""))

    def test_preserves_existing_vary_header(self):
        """Test that mixin preserves existing Vary header values."""

        # Create view that sets its own Vary header
        class TestViewWithVary(LanguageSensitiveMixin, APIView):
            authentication_classes = []  # Disable authentication for test
            permission_classes = []  # Disable permissions for test

            def get(self, request):
                response = Response({"test": "data"})
                response["Vary"] = "Accept, Origin"
                return response

        request = self.factory.get("/test/")
        view = TestViewWithVary.as_view()
        response = view(request)

        vary_header = response.get("Vary", "")
        self.assertIn("Accept", vary_header)
        self.assertIn("Origin", vary_header)
        self.assertIn("Accept-Language", vary_header)
        # Should be formatted as "Accept, Origin, Accept-Language"
        self.assertEqual(vary_header, "Accept, Origin, Accept-Language")

    def test_does_not_duplicate_accept_language(self):
        """Test that mixin doesn't add Accept-Language if already present."""

        class TestViewWithAcceptLanguage(LanguageSensitiveMixin, APIView):
            authentication_classes = []  # Disable authentication for test
            permission_classes = []  # Disable permissions for test

            def get(self, request):
                response = Response({"test": "data"})
                response["Vary"] = "Accept, Accept-Language, Origin"
                return response

        request = self.factory.get("/test/")
        view = TestViewWithAcceptLanguage.as_view()
        response = view(request)

        vary_header = response.get("Vary", "")
        # Should not duplicate Accept-Language
        self.assertEqual(vary_header.count("Accept-Language"), 1)
        self.assertEqual(vary_header, "Accept, Accept-Language, Origin")

    def test_adds_vary_header_when_no_existing_vary(self):
        """Test that mixin adds Vary: Accept-Language when no Vary header exists."""
        request = self.factory.get("/test/")
        view = self.view_class.as_view()
        response = view(request)

        # When no existing Vary header, should be just "Accept-Language"
        vary_header = response.get("Vary", "")
        self.assertIn("Accept-Language", vary_header)
