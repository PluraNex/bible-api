"""Serializers for versions domain."""
from rest_framework import serializers

from ..models import Version


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = [
            "id",
            "name",
            "abbreviation",
            "language",
            "description",
            "is_active",
        ]
