"""Serializers for References domain (T-006)."""
from rest_framework import serializers


class ReferenceParseResponseSerializer(serializers.Serializer):
    input = serializers.CharField()
    items = serializers.ListField(child=serializers.DictField(), help_text="Parsed tokens/ranges")
    warnings = serializers.ListField(child=serializers.CharField(), required=False)


class ReferenceResolveRequestSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    lang = serializers.CharField(required=False)


class ReferenceResolveResponseSerializer(serializers.Serializer):
    results = serializers.ListField(child=serializers.DictField())


class ReferenceNormalizeRequestSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    lang = serializers.CharField(required=False)


class ReferenceNormalizeResponseSerializer(serializers.Serializer):
    normalized = serializers.ListField(child=serializers.DictField())
