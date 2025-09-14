"""Serializers for cross-references domain."""
from rest_framework import serializers

from ..models import CrossReference


class CrossReferenceSerializer(serializers.ModelSerializer):
    # Read-only fields for the book names/codes
    from_book_name = serializers.CharField(source="from_book.name", read_only=True)
    from_book_code = serializers.CharField(source="from_book.osis_code", read_only=True)
    to_book_name = serializers.CharField(source="to_book.name", read_only=True)
    to_book_code = serializers.CharField(source="to_book.osis_code", read_only=True)

    class Meta:
        model = CrossReference
        fields = [
            "id",
            # From reference
            "from_book",
            "from_book_name",
            "from_book_code",
            "from_chapter",
            "from_verse",
            # To reference
            "to_book",
            "to_book_name",
            "to_book_code",
            "to_chapter",
            "to_verse_start",
            "to_verse_end",
            # Metadata
            "source",
            "votes",
            "confidence",
            "explanation",
        ]
        read_only_fields = ["id"]
