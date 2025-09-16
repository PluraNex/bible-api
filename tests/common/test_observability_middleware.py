"""
Tests for observability middleware.
"""
from unittest.mock import Mock, patch
import time

from django.http import HttpRequest, HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import ResolverMatch

from common.observability.middleware import ObservabilityMiddleware


class ObservabilityMiddlewareTest(TestCase):
    """Test ObservabilityMiddleware."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse())

    def test_middleware_initialization(self):
        """Test middleware initializes correctly."""
        with patch('common.observability.middleware.BUILD_INFO') as mock_build_info:
            # Reset to test initialization
            ObservabilityMiddleware._inited = False

            middleware = ObservabilityMiddleware(self.get_response)

            self.assertEqual(middleware.get_response, self.get_response)
            # Should call BUILD_INFO.info on first initialization
            mock_build_info.info.assert_called_once()

    def test_middleware_init_only_once(self):
        """Test that BUILD_INFO is only called once across multiple instances."""
        with patch('common.observability.middleware.BUILD_INFO') as mock_build_info:
            # Reset the class variable
            ObservabilityMiddleware._inited = False

            # First instance should call BUILD_INFO
            middleware1 = ObservabilityMiddleware(self.get_response)
            mock_build_info.info.assert_called_once()

            # Second instance should not call BUILD_INFO again
            mock_build_info.reset_mock()
            middleware2 = ObservabilityMiddleware(self.get_response)
            mock_build_info.info.assert_not_called()

    @patch('common.observability.middleware.LATENCY')
    @patch('common.observability.middleware.REQUESTS')
    @patch('common.observability.middleware.BUILD_INFO')
    def test_call_records_metrics(self, mock_build_info, mock_requests, mock_latency):
        """Test that middleware records latency and request metrics."""
        middleware = ObservabilityMiddleware(self.get_response)

        request = self.factory.get('/test/')
        request.resolver_match = Mock()
        request.resolver_match.view_name = 'test_view'

        response = HttpResponse()
        response.status_code = 200
        self.get_response.return_value = response

        result = middleware(request)

        # Should call LATENCY.labels().observe()
        mock_latency.labels.assert_called_once_with(
            view='test_view',
            lang='unknown',  # No lang provided
            version='default'  # No version provided
        )
        mock_latency.labels().observe.assert_called_once()

        # Should call REQUESTS.labels().inc()
        mock_requests.labels.assert_called_once_with(
            method='GET',
            status='200',
            view='test_view',
            lang='unknown',
            version='default'
        )
        mock_requests.labels().inc.assert_called_once()

        self.assertEqual(result, response)

    @patch('common.observability.middleware.LATENCY')
    @patch('common.observability.middleware.REQUESTS')
    @patch('common.observability.middleware.BUILD_INFO')
    def test_call_with_lang_and_version_params(self, mock_build_info, mock_requests, mock_latency):
        """Test middleware with lang and version parameters."""
        middleware = ObservabilityMiddleware(self.get_response)

        request = self.factory.get('/test/?lang=pt&version=v2')
        request.resolver_match = Mock()
        request.resolver_match.view_name = 'test_view'

        response = HttpResponse()
        response.status_code = 201
        self.get_response.return_value = response

        middleware(request)

        # Should use provided lang and version
        mock_latency.labels.assert_called_once_with(
            view='test_view',
            lang='pt',
            version='v2'
        )

        mock_requests.labels.assert_called_once_with(
            method='GET',
            status='201',
            view='test_view',
            lang='pt',
            version='v2'
        )

    @patch('common.observability.middleware.LATENCY')
    @patch('common.observability.middleware.REQUESTS')
    @patch('common.observability.middleware.BUILD_INFO')
    def test_call_with_lang_code_attribute(self, mock_build_info, mock_requests, mock_latency):
        """Test middleware prefers lang_code attribute over query param."""
        middleware = ObservabilityMiddleware(self.get_response)

        request = self.factory.get('/test/?lang=en')
        request.lang_code = 'pt-BR'  # Should prefer this
        request.resolver_match = Mock()
        request.resolver_match.view_name = 'test_view'

        middleware(request)

        # Should use lang_code attribute, not query param
        mock_latency.labels.assert_called_once_with(
            view='test_view',
            lang='pt-BR',
            version='default'
        )

    @patch('common.observability.middleware.LATENCY')
    @patch('common.observability.middleware.REQUESTS')
    @patch('common.observability.middleware.BUILD_INFO')
    def test_call_handles_resolver_match_exception(self, mock_build_info, mock_requests, mock_latency):
        """Test middleware handles exception when accessing resolver_match."""
        middleware = ObservabilityMiddleware(self.get_response)

        request = self.factory.get('/test/')
        # Simulate exception when accessing resolver_match.view_name
        mock_resolver = Mock()
        type(mock_resolver).view_name = Mock(side_effect=Exception("Test error"))
        request.resolver_match = mock_resolver

        middleware(request)

        # Should use 'unknown' when exception occurs
        mock_latency.labels.assert_called_once_with(
            view='unknown',
            lang='unknown',
            version='default'
        )

    @patch('common.observability.middleware.LATENCY')
    @patch('common.observability.middleware.REQUESTS')
    @patch('common.observability.middleware.BUILD_INFO')
    def test_call_handles_metrics_exception(self, mock_build_info, mock_requests, mock_latency):
        """Test middleware handles exception in metrics recording gracefully."""
        middleware = ObservabilityMiddleware(self.get_response)

        # Make metrics raise exception
        mock_latency.labels.side_effect = Exception("Metrics error")

        request = self.factory.get('/test/')
        request.resolver_match = Mock()
        request.resolver_match.view_name = 'test_view'

        response = HttpResponse()
        self.get_response.return_value = response

        # Should not raise exception, just continue
        result = middleware(request)

        self.assertEqual(result, response)

    @patch('common.observability.middleware.BUILD_INFO')
    def test_init_with_settings_exception(self, mock_build_info):
        """Test initialization handles settings exception gracefully."""
        with patch('django.conf.settings', side_effect=Exception("Settings error")):
            # Reset to test initialization
            ObservabilityMiddleware._inited = False

            middleware = ObservabilityMiddleware(self.get_response)

            # Should call BUILD_INFO with default version
            mock_build_info.info.assert_called_once_with({"service": "bible-api", "version": "v1"})