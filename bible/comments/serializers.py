"""Serializers for commentary domain."""

from rest_framework import serializers

from bible.models import Author, CommentaryEntry, CommentarySource
from bible.verses.serializers import BookNestedSerializer


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for commentary authors."""

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "short_name",
            "author_type",
            "period",
            "century",
            "tradition",
            "theological_school",
            "biography_summary",
        ]


class CommentarySourceSerializer(serializers.ModelSerializer):
    """Serializer for commentary sources."""

    class Meta:
        model = CommentarySource
        fields = [
            "id",
            "name",
            "short_code",
            "publication_year",
            "author_type",
            "description",
            "cover_image_url",
            "is_featured",
            "url",
            "created_at",
        ]


class CommentaryEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for commentary entries with enrichment data.
    """

    author = AuthorSerializer(read_only=True)
    source = CommentarySourceSerializer(read_only=True)
    book = BookNestedSerializer(read_only=True)
    reference = serializers.CharField(source="reference_display", read_only=True)
    length_category = serializers.CharField(read_only=True)

    class Meta:
        model = CommentaryEntry
        fields = [
            "id",
            "source",
            "author",
            "book",
            "chapter",
            "verse_start",
            "verse_end",
            "reference",
            "title",
            "body_text",
            "body_html",
            "original_reference",
            "original_language",
            "word_count",
            "is_complete",
            "confidence_score",
            "length_category",
            # Enrichment fields
            "ai_summary",
            "argumentative_structure",
            "theological_analysis",
            "spiritual_insight",
            "created_at",
            "updated_at",
        ]
