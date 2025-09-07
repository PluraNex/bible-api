"""
Bible API views.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BibleOverviewAPIView(APIView):
    """
    Bible overview endpoint providing basic API information.
    """

    @extend_schema(
        summary="Bible API Overview",
        description="Get basic information about the Bible API",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "api_name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "endpoints": {
                        "type": "object",
                        "properties": {
                            "books": {"type": "string"},
                            "verses": {"type": "string"},
                            "auth": {"type": "string"},
                        },
                    },
                },
            }
        },
    )
    def get(self, request):
        """Get Bible API overview."""
        return Response(
            {
                "api_name": "Bible API",
                "version": "1.0.0",
                "description": "A comprehensive RESTful Bible API with AI integration",
                "endpoints": {
                    "books": "/api/v1/bible/books/",
                    "verses": "/api/v1/bible/verses/",
                    "auth": "/api/v1/auth/",
                },
            },
            status=status.HTTP_200_OK,
        )
