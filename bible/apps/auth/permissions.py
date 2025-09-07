"""
Permission classes for Bible API.
"""
from rest_framework import permissions

from bible.models import APIKey


class HasAPIScopes(permissions.BasePermission):
    """
    Permission class that checks if the authenticated API key has required scopes.

    Usage:
        class MyView(APIView):
            permission_classes = [HasAPIScopes]
            required_scopes = ['read']  # or ['write', 'admin']

    Scopes:
        - 'read': Basic read access to biblical data
        - 'write': Create/update access (bookmarks, notes)
        - 'admin': Administrative access
        - 'ai': AI/LLM integration features
        - 'audio': Text-to-speech synthesis
    """

    def has_permission(self, request, view):
        """
        Check if the request has permission based on required scopes.
        """
        # Allow unauthenticated requests if no scopes required
        required_scopes = getattr(view, "required_scopes", [])
        if not required_scopes:
            return True

        # Check if user is authenticated with API key
        if not request.user or not request.user.is_authenticated:
            return False

        # Get the API key from auth
        if not hasattr(request, "auth") or not isinstance(request.auth, APIKey):
            return False

        api_key = request.auth

        # Check if API key has all required scopes
        for scope in required_scopes:
            if not api_key.has_scope(scope):
                return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions.
        For now, use the same logic as has_permission.
        Can be extended for object-specific scope checking.
        """
        return self.has_permission(request, view)
