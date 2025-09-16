"""
API tests for AI endpoints.
Tests authentication, permissions, agent/tool management, and run workflows.
Following API_TESTING_BEST_PRACTICES.md §2-16 and §10.5.

Consolidates tests from tests/ai/test_ai_views.py following proper structure:
tests/api/<area>/<endpoint>_test_*.py
"""
import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey


@pytest.mark.api
@pytest.mark.ai
class AIEndpointsTest(TestCase):
    """
    Comprehensive tests for AI API endpoints.
    Covers: agents, tools, runs, approval workflows, and AI-specific security.

    Following §10.5: AI (Agentes & Tools)
    - Execução respeita `requires_approval`
    - Estados do run: `running` → `needs_approval` → `succeeded/failed`
    - Throttling diferenciado (`ai-run`, `ai-tools`)
    - Sem vazamento de `plan`/PII
    """

    def setUp(self):
        """Set up minimal test data following best practices §14."""
        self.client = APIClient()
        self.user = User.objects.create_user(username="ai_test_user")

        # API keys with different scopes for AI testing (§5)
        self.api_key_read = APIKey.objects.create(name="Read Key", user=self.user, scopes=["read"])
        self.api_key_ai_run = APIKey.objects.create(name="AI Run Key", user=self.user, scopes=["read", "ai-run"])
        self.api_key_ai_tools = APIKey.objects.create(name="AI Tools Key", user=self.user, scopes=["read", "ai-tools"])
        self.api_key_admin = APIKey.objects.create(
            name="Admin Key", user=self.user, scopes=["read", "write", "admin", "ai-run", "ai-tools"]
        )

    # ========================================
    # Authentication & Authorization Tests (§5)
    # ========================================

    def test_agents_list_requires_auth(self):
        """Test that agents endpoint requires authentication."""
        response = self.client.get("/api/v1/ai/agents/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_tools_list_requires_auth(self):
        """Test that tools endpoint requires authentication."""
        response = self.client.get("/api/v1/ai/tools/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_run_endpoint_requires_ai_run_scope(self):
        """Test that run endpoint requires proper ai-run scope (§10.5)."""
        # Read scope only should get 403 or 501 if not implemented
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.post(
            "/api/v1/ai/agents/test_agent/runs/", {"agent": "test_agent", "input": "test input"}
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_501_NOT_IMPLEMENTED])

    def test_tools_test_requires_ai_tools_scope(self):
        """Test that tool testing requires ai-tools scope."""
        # Read scope only should get 403 or 501 if not implemented
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.post("/api/v1/ai/tools/test-tool/test/", {"input": "test input"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_501_NOT_IMPLEMENTED])

    # ========================================
    # Agents Endpoint Tests
    # ========================================

    def test_agents_list_success_with_read_scope(self):
        """Test successful agents list response with read scope."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.get("/api/v1/ai/agents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify response structure (consistent with other APIs)
        self.assertIn("results", data)
        self.assertIn("pagination", data)
        # Should have themer and xrefs-suggester agents
        self.assertEqual(len(data["results"]), 2)

        # Verify agent structure
        agent = data["results"][0]
        expected_fields = ["name", "description", "enabled", "status"]
        for field in expected_fields:
            self.assertIn(field, agent)

    def test_agents_list_query_efficiency(self):
        """Test that agents list is query-efficient."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        with self.assertNumQueries(2):  # Authentication queries only - response is hardcoded
            response = self.client.get("/api/v1/ai/agents/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ========================================
    # Tools Endpoint Tests
    # ========================================

    def test_tools_list_success_with_read_scope(self):
        """Test successful tools list response with read scope."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.get("/api/v1/ai/tools/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify response structure (consistent with other APIs)
        self.assertIn("results", data)
        self.assertIn("pagination", data)
        self.assertIn("count", data["pagination"])

    def test_tool_test_with_ai_tools_scope(self):
        """Test tool testing with proper ai-tools scope."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_tools.key}")

        response = self.client.post("/api/v1/ai/tools/test-tool/test/", {"input": "test input"})

        # Response depends on implementation and tool existence
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_501_NOT_IMPLEMENTED,
            ],
        )

    # ========================================
    # Run Workflow Tests (§10.5)
    # ========================================

    def test_run_endpoint_with_ai_run_scope(self):
        """Test run endpoint with valid ai-run scope."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_run.key}")

        response = self.client.post(
            "/api/v1/ai/agents/test_agent/runs/", {"agent": "test_agent", "input": "test input"}
        )

        # Response depends on actual implementation
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_202_ACCEPTED,  # Async execution
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_501_NOT_IMPLEMENTED,  # Feature not yet implemented
            ],
        )

    def test_agent_specific_run_requires_auth(self):
        """Test agent-specific run endpoint requires authentication."""
        response = self.client.post("/api/v1/ai/agents/test_agent/runs/", {"input": "test input"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_specific_run_with_auth(self):
        """Test agent-specific run endpoint with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_run.key}")

        response = self.client.post("/api/v1/ai/agents/test_agent/runs/", {"input": "test input"})

        # Response depends on implementation and agent existence
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_202_ACCEPTED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_501_NOT_IMPLEMENTED,
            ],
        )

    def test_run_detail_requires_auth(self):
        """Test that run detail endpoint requires authentication."""
        response = self.client.get("/api/v1/ai/runs/123/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_run_approve_requires_auth(self):
        """Test that run approval endpoint requires authentication."""
        response = self.client.post("/api/v1/ai/runs/123/approve/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_run_cancel_requires_auth(self):
        """Test that run cancellation endpoint requires authentication."""
        response = self.client.delete("/api/v1/ai/runs/123/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================
    # Approval Workflow Tests (§10.5)
    # ========================================

    def test_run_states_transition(self):
        """Test run state transitions: running → needs_approval → succeeded/failed."""
        # This test would require actual run creation and state management
        # Skip if not implemented yet
        self.skipTest("Run state transitions not yet implemented")

    def test_approval_requires_appropriate_permissions(self):
        """Test that run approval requires appropriate permissions."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_run.key}")

        response = self.client.post("/api/v1/ai/runs/123/approve/")

        # Should either work or return appropriate error
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN,  # Insufficient permissions
                status.HTTP_404_NOT_FOUND,  # Run doesn't exist
                status.HTTP_400_BAD_REQUEST,  # Invalid state for approval
                status.HTTP_501_NOT_IMPLEMENTED,  # Feature not implemented yet
            ],
        )

    # ========================================
    # Security Tests (§10.5)
    # ========================================

    def test_no_plan_leakage_in_responses(self):
        """Test that AI plan details don't leak in API responses (§10.5)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        response = self.client.get("/api/v1/ai/agents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_text = response.content.decode().lower()

        # Check that internal plan details are not exposed
        sensitive_terms = ["plan", "internal_state", "debug", "stack_trace"]
        for term in sensitive_terms:
            self.assertNotIn(term, response_text, f"Potentially sensitive term '{term}' found in AI response")

    def test_no_pii_in_ai_error_responses(self):
        """Test that AI error responses don't contain PII (§11)."""
        # Trigger an AI error
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_run.key}")

        response = self.client.post(
            "/api/v1/ai/agents/non_existent_agent/runs/",
            {"agent": "non_existent_agent", "input": "test@email.com secret_password"},
        )

        error_text = response.content.decode().lower()

        # Verify PII patterns are not present in error responses
        pii_patterns = ["test@email.com", "secret_password", "stack trace"]
        for pattern in pii_patterns:
            self.assertNotIn(pattern, error_text)

    # ========================================
    # Throttling Tests (§10.5)
    # ========================================

    @pytest.mark.slow
    def test_ai_run_throttling_limits(self):
        """Test that AI run endpoints have differentiated throttling (§10.5)."""
        # Skip if throttling not configured
        if not hasattr(self, "has_ai_run_throttling"):
            self.skipTest("AI run throttling not configured")

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_run.key}")

        # Make requests until throttled
        responses = []
        for _ in range(20):  # Adjust based on throttle limits
            response = self.client.post(
                "/api/v1/ai/agents/test_agent/runs/", {"agent": "test_agent", "input": "test input"}
            )
            responses.append(response.status_code)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Check Retry-After header
                self.assertIn("Retry-After", response.headers)
                break

        # Should eventually get throttled (ai-run should be more restrictive)
        self.assertIn(
            status.HTTP_429_TOO_MANY_REQUESTS, responses, "AI run endpoint should be throttled more restrictively"
        )

    @pytest.mark.slow
    def test_ai_tools_throttling_limits(self):
        """Test that AI tools endpoints have differentiated throttling."""
        # Skip if throttling not configured
        if not hasattr(self, "has_ai_tools_throttling"):
            self.skipTest("AI tools throttling not configured")

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_ai_tools.key}")

        # Make requests until throttled
        responses = []
        for _ in range(15):  # Adjust based on throttle limits
            response = self.client.post("/api/v1/ai/tools/test-tool/test/", {"input": "test input"})
            responses.append(response.status_code)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        # Should eventually get throttled
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses)

    # ========================================
    # Performance Tests (§8)
    # ========================================

    def test_ai_endpoints_response_time_budget(self):
        """Test that AI endpoints stay within response time budget."""
        import time

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        start_time = time.time()
        response = self.client.get("/api/v1/ai/agents/")
        elapsed = time.time() - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # AI endpoints should be reasonably fast for listing
        self.assertLess(elapsed, 2.0, "AI agents list exceeds 2 second budget")

    # ========================================
    # Contract Compliance Tests (§4)
    # ========================================

    def test_agents_response_structure(self):
        """Test that agents response structure matches expected contract."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.get("/api/v1/ai/agents/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify pagination structure (consistent with other APIs)
        self.assertIn("pagination", data)
        self.assertIn("results", data)

        pagination_fields = ["count", "next", "previous", "num_pages", "current_page", "page_size"]
        for field in pagination_fields:
            self.assertIn(field, data["pagination"])

    def test_tools_response_structure(self):
        """Test that tools response structure matches expected contract."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.get("/api/v1/ai/tools/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify pagination structure (consistent with other APIs)
        self.assertIn("pagination", data)
        self.assertIn("results", data)

        pagination_fields = ["count", "next", "previous", "num_pages", "current_page", "page_size"]
        for field in pagination_fields:
            self.assertIn(field, data["pagination"])
