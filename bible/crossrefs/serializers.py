"""Serializers for cross-references domain."""
from rest_framework import serializers

from ..models import CrossReference


class CrossReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossReference
        fields = ["id", "from_verse", "to_verse", "relationship_type", "source"]
