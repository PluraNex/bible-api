"""Serializers for verses domain."""
from rest_framework import serializers

from ..models import Verse


class VerseSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(read_only=True)

    class Meta:
        model = Verse
        fields = [
            "id",
            "book",
            "version",
            "chapter",
            "number",
            "text",
            "reference",
        ]
