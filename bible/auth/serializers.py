"""
Serializers for authentication endpoints.
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from bible.models import APIKey


class DeveloperRegistrationSerializer(serializers.Serializer):
    """Serializer for developer registration and API key generation."""

    name = serializers.CharField(max_length=100, help_text="Full name of the developer")
    email = serializers.EmailField(help_text="Developer's email address")
    company = serializers.CharField(
        max_length=100, required=False, allow_blank=True, help_text="Company or organization name"
    )
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True, help_text="Brief description of how you plan to use the API"
    )
    website = serializers.URLField(required=False, allow_blank=True, help_text="Your website or app URL")

    def validate_email(self, value):
        """Check if email is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An API key has already been generated for this email address.")
        return value

    def create(self, validated_data):
        """Create user and generate API key."""
        # Create user
        user = User.objects.create_user(
            username=validated_data["email"],  # Use email as username
            email=validated_data["email"],
            first_name=validated_data["name"],
            is_active=True,
        )

        # Create API key with default developer settings
        api_key = APIKey.objects.create(
            name=f"{validated_data['name']} - API Key",
            user=user,
            scopes=["read"],  # Start with read-only access
            rate_limit=1000,  # 1000 requests/hour for new developers
            is_active=True,
        )

        return {
            "user": user,
            "api_key": api_key,
            "company": validated_data.get("company", ""),
            "description": validated_data.get("description", ""),
            "website": validated_data.get("website", ""),
        }


class APIKeyResponseSerializer(serializers.Serializer):
    """Serializer for API key response."""

    api_key = serializers.CharField(help_text="Your API key - keep this secure!")
    name = serializers.CharField(help_text="Developer name")
    email = serializers.EmailField(help_text="Developer email")
    rate_limit = serializers.IntegerField(help_text="Requests per hour limit")
    scopes = serializers.ListField(child=serializers.CharField(), help_text="Available scopes: read, write, ai, audio")
    created_at = serializers.DateTimeField(help_text="API key creation date")
    documentation_url = serializers.URLField(help_text="Link to API documentation")
    examples = serializers.DictField(help_text="Quick start examples")


class APIKeyStatusSerializer(serializers.ModelSerializer):
    """Serializer for API key status and usage."""

    user_name = serializers.CharField(source="user.first_name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    requests_today = serializers.SerializerMethodField()

    class Meta:
        model = APIKey
        fields = [
            "name",
            "user_name",
            "user_email",
            "is_active",
            "rate_limit",
            "scopes",
            "created_at",
            "last_used_at",
            "requests_today",
        ]
        read_only_fields = fields

    def get_requests_today(self, obj):
        """Get requests count for today (placeholder)."""
        # TODO: Implement actual request counting
        return 0
