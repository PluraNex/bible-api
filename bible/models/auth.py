"""
Authentication models for Bible API.
"""
import secrets

from django.contrib.auth.models import User
from django.db import models


class APIKey(models.Model):
    """
    API Key for authentication.
    """

    name = models.CharField(max_length=100, help_text="Descriptive name for this API key")
    key = models.CharField(max_length=64, unique=True, help_text="The actual API key")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Rate limiting and permissions
    rate_limit = models.IntegerField(default=1000, help_text="Requests per hour")
    scopes = models.JSONField(default=list, help_text="List of allowed scopes: ['read', 'write', 'ai', 'audio']")

    class Meta:
        ordering = ["-created_at"]
        db_table = "api_keys"
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"

    def save(self, *args, **kwargs):
        """Generate API key if not provided."""
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        """Generate a secure random API key."""
        return secrets.token_urlsafe(48)

    def has_scope(self, scope):
        """Check if API key has specific scope."""
        return scope in self.scopes

    def update_last_used(self):
        """Update last used timestamp."""
        from django.utils import timezone

        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
