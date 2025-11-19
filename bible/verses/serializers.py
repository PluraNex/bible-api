"""Serializers for verses domain."""

from rest_framework import serializers

from ..models import CanonicalBook, License, Verse, Version


class BookNestedSerializer(serializers.ModelSerializer):
    """Serializer aninhado para livro em verses - domínio simplificado."""

    name = serializers.SerializerMethodField()
    testament_code = serializers.CharField(source="testament.code", read_only=True)

    class Meta:
        model = CanonicalBook
        fields = [
            "osis_code",
            "name",
            "testament_code",
        ]

    def get_name(self, obj):
        """Nome localizado do livro."""
        from bible.utils import get_book_display_name
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_display_name(obj, lang_code)


class VersionNestedSerializer(serializers.ModelSerializer):
    """Serializer aninhado para versão - estrutura simplificada."""

    language_code = serializers.CharField(source="language.code", read_only=True)
    license = serializers.CharField(source="license.code", read_only=True)

    class Meta:
        model = Version
        fields = [
            "code",
            "language_code",
            "license",
            "is_active",
        ]


class VerseSerializer(serializers.ModelSerializer):
    """
    Verse serializer melhorado - frontend-friendly.

    Inclui objetos aninhados para book e version, evitando múltiplas requisições.
    Renomeia 'number' para 'verse' para melhor clareza.
    Resposta otimizada sem campos duplicados.
    """

    # Renomear 'number' para 'verse' (mais intuitivo)
    verse = serializers.IntegerField(source="number", read_only=True)

    # Objetos aninhados (frontend-friendly)
    book = BookNestedSerializer(read_only=True)
    version = VersionNestedSerializer(read_only=True)

    # Language code diretamente no versículo (evita acessar version.language.code)
    language_code = serializers.CharField(source="version.language.code", read_only=True)
    reference = serializers.CharField(read_only=True)

    class Meta:
        model = Verse
        fields = [
            "id",
            "book",
            "version",
            "chapter",
            "verse",
            "text",
            "reference",
            "language_code",
        ]


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
