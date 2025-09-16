"""Serializers for versions domain."""
from rest_framework import serializers

from ..models import Version


class VersionSerializer(serializers.ModelSerializer):
    abbreviation = serializers.ReadOnlyField()
    language = serializers.CharField(source="language.code")

    class Meta:
        model = Version
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "language",
            "description",
            "is_active",
        ]
