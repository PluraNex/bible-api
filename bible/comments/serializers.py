"""Serializers for commentary domain."""

from django.db.models import Count
from rest_framework import serializers

from bible.commentaries import Author, CommentaryEntry, CommentarySource
from bible.verses.serializers import BookNestedSerializer


# ─── Author Serializers ──────────────────────────────────────

class AuthorListSerializer(serializers.ModelSerializer):
    """Compact author for lists and nested use."""

    person_id = serializers.IntegerField(source="person.id", read_only=True, default=None)
    person_slug = serializers.CharField(source="person.slug", read_only=True, default=None)

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "short_name",
            "author_type",
            "tradition",
            "portrait_image",
            "person_id",
            "person_slug",
        ]


class AuthorDetailSerializer(serializers.ModelSerializer):
    """Full author detail with all theological metadata."""

    lifespan = serializers.CharField(read_only=True)
    entry_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "short_name",
            "author_type",
            "birth_year",
            "death_year",
            "lifespan",
            "birthplace",
            "death_location",
            "era",
            "tradition",
            "theological_school",
            "primary_hermeneutic",
            "orthodoxy_status",
            "recognized_by",
            "councils",
            "is_saint",
            "is_doctor_of_church",
            "ecclesiastical_rank",
            "major_works",
            "biography_summary",
            "theological_contributions",
            "portrait_image",
            "wikipedia_url",
            "entry_count",
        ]

    def get_entry_count(self, obj):
        return obj.commentary_entries.count()


# ─── Source Serializers ───────────────────────────────────────

class CommentarySourceSerializer(serializers.ModelSerializer):
    """Serializer for commentary sources."""

    class Meta:
        model = CommentarySource
        fields = [
            "id",
            "name",
            "short_code",
            "source_type",
            "publication_year",
            "author_type",
            "description",
            "cover_image_url",
            "is_featured",
            "url",
            "entry_count",
            "created_at",
        ]


# ─── Entry Serializers ───────────────────────────────────────

# Keep compact author for nested use in entries
AuthorSerializer = AuthorListSerializer


class CommentaryEntrySerializer(serializers.ModelSerializer):
    """Commentary entry with author and source nested."""

    author = AuthorListSerializer(read_only=True)
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
            "created_at",
            "updated_at",
        ]
