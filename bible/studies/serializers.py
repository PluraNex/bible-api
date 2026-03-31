"""Serializers for the studies domain."""

from rest_framework import serializers

from .models import DifficultyLevel, Study, StudyBookmark, StudyType, Visibility
from .services.block_validator import validate_blocks


class StudyListSerializer(serializers.ModelSerializer):
    """Compact serializer for study listings."""

    author_name = serializers.SerializerMethodField()
    block_count = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = [
            "slug",
            "title",
            "subtitle",
            "author_name",
            "study_type",
            "difficulty",
            "visibility",
            "description",
            "cover_image_url",
            "tags",
            "language",
            "is_published",
            "view_count",
            "fork_count",
            "block_count",
            "is_bookmarked",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        user = obj.author
        return user.get_full_name() or user.username

    def get_block_count(self, obj):
        return obj.block_count

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return StudyBookmark.objects.filter(
            study=obj, user=request.user
        ).exists()


class StudyDetailSerializer(serializers.ModelSerializer):
    """Full serializer with blocks for study page view."""

    author_name = serializers.SerializerMethodField()
    block_count = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    forked_from_slug = serializers.SerializerMethodField()
    source_topic_slug = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = [
            "slug",
            "title",
            "subtitle",
            "author_name",
            "study_type",
            "difficulty",
            "visibility",
            "blocks",
            "description",
            "cover_image_url",
            "tags",
            "language",
            "source_plan_id",
            "source_topic_slug",
            "source_validation_id",
            "is_published",
            "published_at",
            "view_count",
            "fork_count",
            "forked_from_slug",
            "block_count",
            "is_bookmarked",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        user = obj.author
        return user.get_full_name() or user.username

    def get_block_count(self, obj):
        return obj.block_count

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return StudyBookmark.objects.filter(
            study=obj, user=request.user
        ).exists()

    def get_forked_from_slug(self, obj):
        return obj.forked_from.slug if obj.forked_from else None

    def get_source_topic_slug(self, obj):
        return obj.source_topic.slug if obj.source_topic else None


class StudyRailSerializer(serializers.ModelSerializer):
    """
    Compact serializer for the study rail panel.

    Returns metadata + first few paragraphs as preview.
    Does NOT return the full blocks array.
    """

    author_name = serializers.SerializerMethodField()
    block_count = serializers.SerializerMethodField()
    preview_blocks = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = [
            "slug",
            "title",
            "subtitle",
            "author_name",
            "study_type",
            "difficulty",
            "description",
            "cover_image_url",
            "tags",
            "block_count",
            "preview_blocks",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        user = obj.author
        return user.get_full_name() or user.username

    def get_block_count(self, obj):
        return obj.block_count

    def get_preview_blocks(self, obj):
        """Return first 3 text/paragraph blocks as preview."""
        if not obj.blocks:
            return []

        preview = []
        for block in obj.blocks:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype in ("paragraph", "heading", "verse_cite", "callout"):
                preview.append(block)
                if len(preview) >= 3:
                    break
        return preview


class StudyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating studies with block validation."""

    class Meta:
        model = Study
        fields = [
            "title",
            "subtitle",
            "study_type",
            "difficulty",
            "visibility",
            "blocks",
            "description",
            "cover_image_url",
            "tags",
            "language",
            "source_plan_id",
        ]

    def validate_study_type(self, value):
        if value and value not in StudyType.values:
            raise serializers.ValidationError(
                f"Invalid study_type. Must be one of: {', '.join(StudyType.values)}"
            )
        return value

    def validate_difficulty(self, value):
        if value and value not in DifficultyLevel.values:
            raise serializers.ValidationError(
                f"Invalid difficulty. Must be one of: {', '.join(DifficultyLevel.values)}"
            )
        return value

    def validate_visibility(self, value):
        if value and value not in Visibility.values:
            raise serializers.ValidationError(
                f"Invalid visibility. Must be one of: {', '.join(Visibility.values)}"
            )
        return value

    def validate_blocks(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("blocks must be a list")

        errors = validate_blocks(value)
        if errors:
            raise serializers.ValidationError(errors)

        return value

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        from django.utils.text import slugify

        User = get_user_model()

        title = validated_data.get("title", "")
        base_slug = slugify(title)[:180]
        slug = base_slug

        # Ensure uniqueness
        counter = 1
        while Study.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        validated_data["slug"] = slug

        # Use authenticated user or fallback to curated user
        user = self.context["request"].user
        if user.is_authenticated:
            validated_data["author"] = user
        else:
            validated_data["author"], _ = User.objects.get_or_create(
                username="bible-api-curated", defaults={"is_active": True}
            )

        return super().create(validated_data)


class StudyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for partial updates to studies."""

    class Meta:
        model = Study
        fields = [
            "title",
            "subtitle",
            "study_type",
            "difficulty",
            "visibility",
            "blocks",
            "description",
            "cover_image_url",
            "tags",
            "language",
        ]

    def validate_blocks(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("blocks must be a list")

        errors = validate_blocks(value)
        if errors:
            raise serializers.ValidationError(errors)

        return value
