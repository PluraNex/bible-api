"""
Frontend-optimized serializers for books domain.
"""

from rest_framework import serializers

from ..models import CanonicalBook


class TestamentNestedSerializer(serializers.Serializer):
    """Testament nested object."""

    id = serializers.CharField()
    name = serializers.CharField()
    code = serializers.CharField()


class FrontendBookSerializer(serializers.ModelSerializer):
    """
    Frontend-optimized book serializer.

    Returns data ready to use - zero transformation needed.
    """

    id = serializers.CharField()
    osisCode = serializers.CharField(source="osis_code")
    name = serializers.SerializerMethodField()
    abbreviation = serializers.SerializerMethodField()
    canonicalOrder = serializers.IntegerField(source="canonical_order")
    testament = TestamentNestedSerializer(source="testament", read_only=True)
    chapterCount = serializers.IntegerField(source="chapter_count")
    isDeuterocanonical = serializers.BooleanField(source="is_deuterocanonical")

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

    class Meta:
        model = CanonicalBook
        fields = [
            "id",
            "osisCode",
            "name",
            "abbreviation",
            "canonicalOrder",
            "testament",
            "chapterCount",
            "isDeuterocanonical",
        ]
