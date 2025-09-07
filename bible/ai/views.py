"""
AI Agent and Tool views for Bible API.
Skeleton implementation for T-001.
"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class AgentListView(generics.ListAPIView):
    """List available AI agents."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "agents": [
                    {
                        "name": "themer",
                        "description": "AI agent for theme analysis and tagging",
                        "enabled": False,
                        "status": "not_implemented",
                    },
                    {
                        "name": "xrefs-suggester",
                        "description": "AI agent for cross-reference suggestions",
                        "enabled": False,
                        "status": "not_implemented",
                    },
                ]
            },
            status=status.HTTP_200_OK,
        )


class ToolListView(generics.ListAPIView):
    """List available AI tools."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "tools": [
                    {
                        "name": "apply_theme_tags",
                        "description": "Apply theme tags to verses",
                        "requires_approval": True,
                        "status": "not_implemented",
                    },
                    {
                        "name": "suggest_cross_references",
                        "description": "Suggest cross references for verses",
                        "requires_approval": True,
                        "status": "not_implemented",
                    },
                ]
            },
            status=status.HTTP_200_OK,
        )


class ToolTestView(APIView):
    """Test an AI tool (skeleton)."""

    def post(self, request, tool, *args, **kwargs):
        return Response(
            {
                "tool": tool,
                "status": "test_not_implemented",
                "message": "AI tools testing not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunCreateView(generics.CreateAPIView):
    """Create a new agent run."""

    def post(self, request, name, *args, **kwargs):
        return Response(
            {
                "agent": name,
                "status": "agent_runs_not_implemented",
                "message": "AI agent runs not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunDetailView(generics.RetrieveAPIView):
    """Get details of an agent run."""

    def get(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "agent_runs_not_implemented",
                "message": "AI agent runs not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunApproveView(APIView):
    """Approve an agent run."""

    def post(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "approval_not_implemented",
                "message": "AI agent run approval not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunCancelView(APIView):
    """Cancel an agent run."""

    def delete(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "cancellation_not_implemented",
                "message": "AI agent run cancellation not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
