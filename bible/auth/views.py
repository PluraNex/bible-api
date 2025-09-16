"""
Authentication views for Bible API.
"""
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.openapi import get_error_responses

from .serializers import (
    APIKeyResponseSerializer,
    DeveloperRegistrationSerializer,
)


class AuthStatusAPIView(APIView):
    """
    Authentication status endpoint.
    """
    permission_classes = [AllowAny]

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


class DeveloperRegistrationAPIView(APIView):
    """
    Developer registration endpoint for API key generation.
    """

    permission_classes = [AllowAny]  # Anyone can register

    @extend_schema(
        summary="Register for API Access",
        description="""
        Register as a developer and receive an API key for accessing the Bible API.

        **What you'll get:**
        - Instant API key generation
        - 1,000 requests/hour rate limit
        - Read access to all endpoints
        - Complete documentation and examples

        **Perfect for:**
        - Mobile app developers
        - Web developers
        - Scripture study applications
        - Educational projects
        """,
        tags=["auth"],
        request=DeveloperRegistrationSerializer,
        responses={201: APIKeyResponseSerializer, **get_error_responses()},
        examples=[
            OpenApiExample("Basic Registration", value={"name": "João Silva", "email": "joao@exemplo.com"}),
            OpenApiExample(
                "Complete Registration",
                value={
                    "name": "Maria Santos",
                    "email": "maria@startup.com",
                    "company": "BibliaApp LTDA",
                    "description": "Aplicativo mobile de estudos bíblicos para jovens",
                    "website": "https://bibliaapp.com",
                },
            ),
        ],
    )
    def post(self, request):
        """Register a new developer and generate API key."""
        serializer = DeveloperRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()

            # Prepare response with examples
            api_key = result["api_key"]
            user = result["user"]
            base_url = request.build_absolute_uri("/").rstrip("/")

            response_data = {
                "api_key": api_key.key,
                "name": user.first_name,
                "email": user.email,
                "rate_limit": api_key.rate_limit,
                "scopes": api_key.scopes,
                "created_at": api_key.created_at,
                "documentation_url": f"{base_url}/api/v1/docs/",
                "examples": {
                    "curl": f"""curl -H "Authorization: Api-Key {api_key.key}" \\
     {base_url}/api/v1/bible/books/""",
                    "javascript": f"""fetch('{base_url}/api/v1/bible/books/', {{
  headers: {{ 'Authorization': 'Api-Key {api_key.key}' }}
}})
.then(response => response.json())
.then(data => console.log(data));""",
                    "python": f"""import requests

headers = {{'Authorization': 'Api-Key {api_key.key}'}}
response = requests.get('{base_url}/api/v1/bible/books/', headers=headers)
data = response.json()
print(data)""",
                },
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
