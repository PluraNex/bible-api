"""Serializers for the Person hub."""

from rest_framework import serializers

from .models import Person


class PersonListSerializer(serializers.ModelSerializer):
    """Compact person for lists."""

    has_author_profile = serializers.BooleanField(read_only=True)
    has_biblical_profile = serializers.BooleanField(read_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "canonical_name",
            "slug",
            "person_type",
            "portrait_image",
            "has_author_profile",
            "has_biblical_profile",
        ]


class PersonDetailSerializer(serializers.ModelSerializer):
    """Full person detail with profile links."""

    has_author_profile = serializers.BooleanField(read_only=True)
    has_biblical_profile = serializers.BooleanField(read_only=True)
    author_profile = serializers.SerializerMethodField()
    biblical_profile = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            "id",
            "canonical_name",
            "slug",
            "person_type",
            "birth_year",
            "death_year",
            "description",
            "wikipedia_url",
            "portrait_image",
            "has_author_profile",
            "has_biblical_profile",
            "author_profile",
            "biblical_profile",
            "created_at",
        ]

    def get_author_profile(self, obj):
        if not obj.has_author_profile:
            return None
        ap = obj.author_profile
        return {
            "id": ap.id,
            "author_type": ap.author_type,
            "tradition": ap.tradition,
            "primary_hermeneutic": ap.primary_hermeneutic,
            "orthodoxy_status": ap.orthodoxy_status,
            "is_doctor_of_church": ap.is_doctor_of_church,
            "entry_count": ap.commentary_entries.count(),
        }

    def get_biblical_profile(self, obj):
        if not obj.has_biblical_profile:
            return None
        bp = obj.biblical_profile
        return {
            "canonical_id": bp.canonical_id,
            "namespace": bp.namespace,
            "primary_name": bp.primary_name,
        }
