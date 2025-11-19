"""Shared serializers for bible domain - avoiding circular imports."""

from rest_framework import serializers

from .models import BookCategory, Testament


class TestamentSerializer(serializers.ModelSerializer):
    """Shared serializer for Testament - simplified structure with localization."""

    code = serializers.CharField(read_only=True)  # Usa a property do modelo
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Testament
        fields = ["code", "name", "description", "order"]
        read_only_fields = fields

    def get_name(self, obj):
        """Nome localizado do testamento."""
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return obj.get_display_name(lang_code)

    def get_description(self, obj):
        """Descrição localizada do testamento."""
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return obj.get_description(lang_code)


class BookCategorySerializer(serializers.ModelSerializer):
    """Serializer para categorias de livros com localização."""

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = BookCategory
        fields = ["id", "name", "description", "order"]
        read_only_fields = fields

    def get_name(self, obj):
        """Retorna nome localizado."""
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return obj.get_name(lang_code)

    def get_description(self, obj):
        """Retorna descrição localizada."""
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return obj.get_description(lang_code)
