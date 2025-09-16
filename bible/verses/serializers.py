"""Serializers for verses domain."""
from rest_framework import serializers

from ..models import License, Verse, Version


class VerseSerializer(serializers.ModelSerializer):
    """Verse serializer with enhanced blueprint support."""

    reference = serializers.CharField(read_only=True)
    book_osis = serializers.CharField(source="book.osis_code", read_only=True)
    book_name = serializers.SerializerMethodField()
    version_code = serializers.CharField(source="version.code", read_only=True)

    class Meta:
        model = Verse
        fields = [
            "id",
            "book",
            "book_osis",
            "book_name",
            "version",
            "version_code",
            "chapter",
            "number",
            "text",
            "reference",
            "created_at",
            "updated_at",
        ]

    def get_book_name(self, obj) -> str:
        """Get localized book name using standardized utility with fallback logic."""
        from bible.utils import get_book_display_name
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_display_name(obj.book, lang_code)


class VersionSerializer(serializers.ModelSerializer):
    """Enhanced version serializer with blueprint support."""

    language_code = serializers.CharField(source="language.code", read_only=True)
    language_name = serializers.CharField(source="language.name", read_only=True)
    license_code = serializers.CharField(source="license.code", read_only=True)
    license_name = serializers.CharField(source="license.name", read_only=True)
    abbreviation = serializers.CharField(read_only=True)  # Computed property

    class Meta:
        model = Version
        fields = [
            "id",
            "code",
            "name",
            "abbreviation",
            "language",
            "language_code",
            "language_name",
            "versification",
            "copyright",
            "permissions",
            "license",
            "license_code",
            "license_name",
            "source_url",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]


class LicenseSerializer(serializers.ModelSerializer):
    """License information serializer."""

    class Meta:
        model = License
        fields = ["id", "code", "name", "url", "created_at", "updated_at"]
