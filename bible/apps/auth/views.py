"""
Authentication views for Bible API.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class AuthStatusAPIView(APIView):
    """
    Authentication status endpoint.
    """

    @extend_schema(
        summary="Authentication Status",
        description="Check current authentication status",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "authenticated": {"type": "boolean"},
                    "user": {"type": "string"},
                    "api_key_status": {"type": "string"},
                },
            }
        },
    )
    def get(self, request):
        """Get authentication status."""
        return Response(
            {
                "authenticated": request.user.is_authenticated,
                "user": str(request.user) if request.user.is_authenticated else None,
                "api_key_status": "active" if request.user.is_authenticated else "required",
            },
            status=status.HTTP_200_OK,
        )
