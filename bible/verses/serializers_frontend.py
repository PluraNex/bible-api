"""
Frontend-optimized serializers for verses domain.
These serializers return data in frontend-friendly format (camelCase, nested objects, string IDs).
Use with ?format=frontend query parameter.
"""

from rest_framework import serializers

from ..models import Verse, CanonicalBook, Version


class BookNestedSerializer(serializers.Serializer):
    """Book object nested in verse response - frontend optimized."""

    id = serializers.CharField()
    osisCode = serializers.CharField(source="osis_code")
    name = serializers.SerializerMethodField()
    abbreviation = serializers.SerializerMethodField()

    def get_name(self, obj):
        """Get localized book name."""
        from bible.utils import get_book_display_name
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_display_name(obj, lang_code)

    def get_abbreviation(self, obj):
        """Get localized book abbreviation."""
        from bible.utils import get_book_abbreviation
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_abbreviation(obj, lang_code)


class VersionNestedSerializer(serializers.Serializer):
    """Version object nested in verse response - frontend optimized."""

    id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    abbreviation = serializers.CharField()
    language = serializers.CharField(source="language.code")


class FrontendVerseSerializer(serializers.ModelSerializer):
    """
    Frontend-optimized verse serializer.

    Returns data ready to use in frontend - zero transformation needed:
    - IDs as strings
    - camelCase field names
    - Nested objects (book, version) instead of just IDs
    - All necessary fields included

    Usage: Add ?format=frontend to endpoint URL
    """

    id = serializers.CharField()  # String, not number
    book = BookNestedSerializer(read_only=True)  # Full object, not just ID
    chapter = serializers.IntegerField()
    verse = serializers.IntegerField(source="number")  # Named 'verse' not 'number'
    text = serializers.CharField()
    version = VersionNestedSerializer(read_only=True)  # Full object, not just ID
    reference = serializers.CharField(read_only=True)
    language = serializers.CharField(source="version.language.code", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at")  # camelCase
    updatedAt = serializers.DateTimeField(source="updated_at")  # camelCase

    class Meta:
        model = Verse
        fields = [
            "id",
            "book",
            "chapter",
            "verse",
            "text",
            "version",
            "reference",
            "language",
            "createdAt",
            "updatedAt",
        ]
