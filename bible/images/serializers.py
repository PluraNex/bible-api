"""Serializers for Biblical Images domain."""

from rest_framework import serializers

from .models import Artist, BiblicalImage, ImageTag, ImageVerseLink


# ─── Artist ───────────────────────────────────────────────

class ArtistListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ["id", "name", "slug", "nations", "movements", "image_count"]


class ArtistDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            "id", "name", "slug", "birth_date", "death_date",
            "nations", "movements", "image_count", "source",
        ]


# ─── Image Tag (nested) ──────────────────────────────────

class ImageTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageTag
        fields = [
            "characters", "event", "tag_list", "symbols",
            "description", "theological_description",
            "scripture_refs", "scene_type", "moods", "period",
        ]


# ─── Verse Link (nested) ─────────────────────────────────

class ImageVerseLinkSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.osis_code", read_only=True)

    class Meta:
        model = ImageVerseLink
        fields = ["book", "chapter", "verse_start", "verse_end", "relevance_type", "reason"]


# ─── Biblical Image ──────────────────────────────────────

class BiblicalImageListSerializer(serializers.ModelSerializer):
    """Compact for lists and by-verse results."""

    artist_name = serializers.CharField(source="artist.name", read_only=True)
    artist_slug = serializers.CharField(source="artist.slug", read_only=True)

    class Meta:
        model = BiblicalImage
        fields = [
            "id", "key", "title", "artist_name", "artist_slug",
            "completion_year", "image_url", "thumbnail_url",
            "is_tagged", "styles", "genres",
        ]


class BiblicalImageDetailSerializer(serializers.ModelSerializer):
    """Full detail with nested tag + verse links."""

    artist = ArtistDetailSerializer(read_only=True)
    tag = ImageTagSerializer(read_only=True)
    verse_links = ImageVerseLinkSerializer(many=True, read_only=True)

    class Meta:
        model = BiblicalImage
        fields = [
            "id", "key", "title", "artist",
            "completion_year", "styles", "genres", "media",
            "width", "height", "image_url", "thumbnail_url",
            "is_tagged", "source",
            "tag", "verse_links",
            "created_at",
        ]


class BiblicalImageByVerseSerializer(serializers.Serializer):
    """Focused response for by-verse endpoint (ArtsTab)."""

    id = serializers.IntegerField()
    key = serializers.CharField()
    title = serializers.CharField()
    artist_name = serializers.CharField()
    completion_year = serializers.IntegerField(allow_null=True)
    image_url = serializers.URLField()
    thumbnail_url = serializers.URLField()
    relevance_type = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    characters = serializers.ListField(default=[])
