"""
AI Agent and Tool views for Bible API.
Skeleton implementation with auth and schema annotations.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView


class AgentListView(generics.ListAPIView):
    """List available AI agents."""

    @extend_schema(
        summary="List AI agents",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "agents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "enabled": {"type": "boolean"},
                                "status": {"type": "string"},
                            },
                        },
                    }
                },
            }
        },
    )
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

    @extend_schema(
        summary="List AI tools",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "tools": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "requires_approval": {"type": "boolean"},
                                "status": {"type": "string"},
                            },
                        },
                    }
                },
            }
        },
    )
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

    @extend_schema(
        summary="Test an AI tool",
        responses={
            501: {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    def post(self, request, tool, *args, **kwargs):
        return Response(
            {
                "tool": tool,
                "status": "test_not_implemented",
                "message": "AI tools testing not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunCreateView(APIView):
    """Create a new agent run (skeleton)."""

    @extend_schema(
        summary="Create agent run",
        responses={
            501: {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    def post(self, request, name, *args, **kwargs):
        return Response(
            {
                "agent": name,
                "status": "agent_runs_not_implemented",
                "message": "AI agent runs not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunDetailView(APIView):
    """Get details of an agent run (skeleton)."""

    @extend_schema(
        summary="Get agent run details",
        responses={
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
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

    @extend_schema(
        summary="Approve agent run",
        responses={
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
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

    @extend_schema(
        summary="Cancel agent run",
        responses={
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    def delete(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "cancellation_not_implemented",
                "message": "AI agent run cancellation not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
