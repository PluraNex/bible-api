# 📚 Proposta: Topics Domain (Tópicos Bíblicos)

## Visão Geral

Os **Topics** são diferentes dos **Themes**:
- **Theme** = Conceito teológico abstrato (ex: "Salvação", "Fé", "Amor")
- **Topic** = Entrada enciclopédica completa (ex: "ABRAHAM", "BAPTISM", "SALVATION")

Um Topic pode conter múltiplos Themes, Entities e Symbols extraídos pelo pipeline.

### 🌍 Suporte a Múltiplos Idiomas

Seguindo o padrão de `BookName`, os Topics suportam internacionalização:

1. **Topic** = Entrada canônica (language-agnostic)
2. **TopicName** = Nomes/aliases por idioma (como `BookName`)
3. **TopicContent** = Conteúdo localizado (summary, outline, etc.)

Os endpoints usam:
- Query param: `?lang=pt` (prioridade)
- Header: `Accept-Language: pt-BR`
- Fallback: `pt-BR` → `pt` → `en`

---

## 📊 Modelos Django

### `bible/models/topics.py`

```python
"""
Topic models for Bible API (topical references/encyclopedia entries).
Follows the BookName pattern for i18n support.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

from .books import Language
from .verses import Verse


class Topic(models.Model):
    """
    Biblical topic/encyclopedia entry from Nave's, Torrey's, etc.
    
    Canonical entry - language-agnostic.
    Names and content are stored in TopicName and TopicContent.
    """
    
    # Identificação
    slug = models.SlugField(max_length=150, unique=True, db_index=True)
    canonical_id = models.CharField(max_length=100, unique=True)  # "UNIFIED:abraham"
    
    # Nome canônico (inglês como base, usado para busca)
    canonical_name = models.CharField(max_length=200)  # "ABRAHAM"
    name_normalized = models.CharField(max_length=200, db_index=True)  # "abraham"
    
    # Fontes
    primary_source = models.CharField(max_length=10)  # "NAV", "TOR"
    available_sources = ArrayField(models.CharField(max_length=10), default=list)
    
    # Estatísticas (language-agnostic)
    total_verses = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)
    books_count = models.IntegerField(default=0)
    aspects_count = models.IntegerField(default=0)
    
    # AI Enrichment
    ai_enriched = models.BooleanField(default=False)
    ai_model = models.CharField(max_length=50, blank=True)
    ai_confidence = models.FloatField(default=0.0)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    
    # Qualidade
    quality_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topics"
        ordering = ["name_normalized"]
        indexes = [
            models.Index(fields=["name_normalized"]),
            models.Index(fields=["primary_source"]),
            models.Index(fields=["ai_enriched"]),
        ]

    def __str__(self):
        return self.canonical_name
    
    def get_display_name(self, language_code="en"):
        """Get localized display name with fallback logic."""
        # Try exact match
        name_obj = self.names.filter(
            language__code=language_code
        ).first()
        if name_obj:
            return name_obj.name
        
        # Fallback: pt-BR -> pt
        if language_code.startswith("pt"):
            name_obj = self.names.filter(language__code="pt").first()
            if name_obj:
                return name_obj.name
        
        # Fallback: en
        name_obj = self.names.filter(language__code="en").first()
        if name_obj:
            return name_obj.name
        
        return self.canonical_name


class TopicName(models.Model):
    """
    Topic names and aliases by language.
    Follows the BookName pattern.
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="names")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="topic_names")
    
    name = models.CharField(max_length=200)  # "Abraão" (pt), "Abraham" (en)
    aliases = ArrayField(models.CharField(max_length=200), default=list, blank=True)  # ["Abrão"]
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_names"
        ordering = ["topic", "language"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "language"],
                name="uniq_topic_name_per_language",
            ),
        ]
        indexes = [
            models.Index(fields=["topic", "language"], name="topicname_topic_lang_idx"),
            models.Index(fields=["name"]),
            GinIndex(fields=["aliases"], name="topicname_aliases_gin"),
        ]

    def __str__(self):
        return f"{self.name} [{self.language.code}]"


class TopicContent(models.Model):
    """
    Localized content for a Topic.
    Allows summary, outline, and theological content in multiple languages.
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="contents")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="topic_contents")
    
    # Conteúdo localizado
    summary = models.TextField(blank=True)  # AI-generated summary
    outline = ArrayField(models.TextField(), default=list, blank=True)
    key_concepts = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    theological_significance = models.TextField(blank=True)
    
    # Raw content (original source material)
    primary_content = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_contents"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "language"],
                name="uniq_topic_content_per_language",
            ),
        ]
        indexes = [
            models.Index(fields=["topic", "language"], name="topiccontent_topic_lang_idx"),
        ]

    def __str__(self):
        return f"Content for {self.topic.slug} [{self.language.code}]"


class TopicAspect(models.Model):
    """
    Structured aspect/subtopic within a Topic.
    
    Ex: Para ABRAHAM: "Divine call of", "God's covenant with", etc.
    Aspects have localized labels via TopicAspectName.
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="aspects")
    
    # Canonical label (English)
    canonical_label = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
    
    # Estatísticas do aspecto
    verse_count = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)
    
    # Livros onde aparece (OSIS codes)
    books = ArrayField(models.CharField(max_length=20), default=list)

    class Meta:
        db_table = "topic_aspects"
        ordering = ["topic", "order"]
        indexes = [
            models.Index(fields=["topic", "order"]),
        ]

    def __str__(self):
        return f"{self.topic.slug}: {self.canonical_label[:50]}"
    
    def get_label(self, language_code="en"):
        """Get localized label with fallback logic."""
        label_obj = self.labels.filter(language__code=language_code).first()
        if label_obj:
            return label_obj.label
        
        # Fallback
        if language_code.startswith("pt"):
            label_obj = self.labels.filter(language__code="pt").first()
            if label_obj:
                return label_obj.label
        
        label_obj = self.labels.filter(language__code="en").first()
        if label_obj:
            return label_obj.label
        
        return self.canonical_label


class TopicAspectLabel(models.Model):
    """
    Localized labels for TopicAspect.
    """
    
    aspect = models.ForeignKey(TopicAspect, on_delete=models.CASCADE, related_name="labels")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="aspect_labels")
    
    label = models.CharField(max_length=500)  # "Chamado divino de" (pt)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_aspect_labels"
        constraints = [
            models.UniqueConstraint(
                fields=["aspect", "language"],
                name="uniq_aspect_label_per_language",
            ),
        ]

    def __str__(self):
        return f"{self.label[:50]} [{self.language.code}]"


class TopicVerse(models.Model):
    """
    Association between a Topic and a Verse.
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="verse_links")
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="topic_links")
    aspect = models.ForeignKey(TopicAspect, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contexto da referência
    relevance_score = models.FloatField(default=1.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_verses"
        constraints = [
            models.UniqueConstraint(fields=["topic", "verse"], name="uniq_topic_verse"),
        ]
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["verse"]),
        ]

    def __str__(self):
        return f"{self.topic.slug} ~ {self.verse.reference}"


class TopicTheme(models.Model):
    """
    Themes extracted from a Topic (via AI).
    
    Conecta Topic -> Theme com contexto.
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="theme_links")
    theme = models.ForeignKey("Theme", on_delete=models.CASCADE, related_name="topic_sources")
    
    aspect = models.CharField(max_length=500, blank=True)  # "Qual aspecto do tópico este tema representa"
    confidence = models.FloatField(default=1.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_themes"
        constraints = [
            models.UniqueConstraint(fields=["topic", "theme"], name="uniq_topic_theme"),
        ]

    def __str__(self):
        return f"{self.topic.slug} -> {self.theme.name}"


class TopicEntity(models.Model):
    """
    Entities mentioned in a Topic (via AI).
    Links to canonical entities in the gazetteer.
    """
    
    ENTITY_TYPES = [
        ("PERSON", "Person"),
        ("PLACE", "Place"),
        ("EVENT", "Event"),
        ("OBJECT", "Object"),
        ("CONCEPT", "Concept"),
        ("DEITY", "Deity"),
        ("LITERARY_WORK", "Literary Work"),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="entity_links")
    
    # Canonical entity reference (from gazetteer)
    canonical_entity_id = models.CharField(max_length=100, db_index=True)  # "PERSON:abraham"
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    
    # Role in context (localized via TopicEntityRole)
    role_canonical = models.CharField(max_length=500, blank=True)  # "patriarch of Israel"
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_entities"
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["entity_type"]),
            models.Index(fields=["canonical_entity_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "canonical_entity_id"],
                name="uniq_topic_entity",
            ),
        ]

    def __str__(self):
        return f"{self.topic.slug}: {self.canonical_entity_id}"


class CanonicalEntity(models.Model):
    """
    Canonical entity from the gazetteer.
    Stores display names and metadata per language.
    """
    
    ENTITY_TYPES = [
        ("PERSON", "Person"),
        ("PLACE", "Place"),
        ("EVENT", "Event"),
        ("OBJECT", "Object"),
        ("CONCEPT", "Concept"),
        ("DEITY", "Deity"),
        ("LITERARY_WORK", "Literary Work"),
    ]
    
    canonical_id = models.CharField(max_length=100, unique=True, db_index=True)  # "PERSON:abraham"
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    
    # Frequency/importance
    frequency = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_entities"
        indexes = [
            models.Index(fields=["entity_type"]),
            models.Index(fields=["frequency"]),
        ]

    def __str__(self):
        return self.canonical_id
    
    def get_display_name(self, language_code="en"):
        """Get localized display name."""
        name_obj = self.names.filter(language__code=language_code).first()
        if name_obj:
            return name_obj.display_name
        
        # Fallback
        if language_code.startswith("pt"):
            name_obj = self.names.filter(language__code="pt").first()
            if name_obj:
                return name_obj.display_name
        
        name_obj = self.names.filter(language__code="en").first()
        if name_obj:
            return name_obj.display_name
        
        # Extract from canonical_id
        return self.canonical_id.split(":")[-1].replace("_", " ").title()


class CanonicalEntityName(models.Model):
    """
    Localized names for CanonicalEntity.
    """
    
    entity = models.ForeignKey(CanonicalEntity, on_delete=models.CASCADE, related_name="names")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="entity_names")
    
    display_name = models.CharField(max_length=200)  # "Abraão" (pt), "Abraham" (en)
    aliases = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_entity_names"
        constraints = [
            models.UniqueConstraint(
                fields=["entity", "language"],
                name="uniq_entity_name_per_language",
            ),
        ]
        indexes = [
            models.Index(fields=["display_name"]),
            GinIndex(fields=["aliases"], name="entityname_aliases_gin"),
        ]

    def __str__(self):
        return f"{self.display_name} [{self.language.code}]"


class TopicSymbol(models.Model):
    """
    Biblical symbols mentioned in a Topic (via AI).
    Links to canonical symbols in the gazetteer.
    """
    
    SYMBOL_TYPES = [
        ("NATURAL", "Natural Element"),
        ("OBJECT", "Object"),
        ("ACTION", "Action"),
        ("NUMBER", "Number"),
        ("COLOR", "Color"),
        ("DIRECTION", "Direction"),
        ("PERSON_TYPE", "Person Type"),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="symbol_links")
    
    # Canonical symbol reference (from gazetteer)
    canonical_symbol_id = models.CharField(max_length=100, db_index=True)  # "NATURAL:water"
    symbol_type = models.CharField(max_length=20, choices=SYMBOL_TYPES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_symbols"
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["symbol_type"]),
            models.Index(fields=["canonical_symbol_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "canonical_symbol_id"],
                name="uniq_topic_symbol",
            ),
        ]

    def __str__(self):
        return f"{self.topic.slug}: {self.canonical_symbol_id}"


class CanonicalSymbol(models.Model):
    """
    Canonical symbol from the gazetteer.
    Stores meanings and visual correlations per language.
    """
    
    SYMBOL_TYPES = [
        ("NATURAL", "Natural Element"),
        ("OBJECT", "Object"),
        ("ACTION", "Action"),
        ("NUMBER", "Number"),
        ("COLOR", "Color"),
        ("DIRECTION", "Direction"),
        ("PERSON_TYPE", "Person Type"),
    ]
    
    canonical_id = models.CharField(max_length=100, unique=True, db_index=True)  # "NATURAL:water"
    symbol_type = models.CharField(max_length=20, choices=SYMBOL_TYPES)
    
    # Frequency/importance
    frequency = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_symbols"
        indexes = [
            models.Index(fields=["symbol_type"]),
            models.Index(fields=["frequency"]),
        ]

    def __str__(self):
        return self.canonical_id


class CanonicalSymbolContent(models.Model):
    """
    Localized content for CanonicalSymbol.
    """
    
    symbol = models.ForeignKey(CanonicalSymbol, on_delete=models.CASCADE, related_name="contents")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="symbol_contents")
    
    display_name = models.CharField(max_length=200)  # "Água" (pt), "Water" (en)
    literal_meaning = models.TextField(blank=True)
    symbolic_meanings = ArrayField(models.TextField(), default=list)
    visual_correlations = ArrayField(models.CharField(max_length=200), default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_symbol_contents"
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "language"],
                name="uniq_symbol_content_per_language",
            ),
        ]

    def __str__(self):
        return f"{self.display_name} [{self.language.code}]"


class TopicRelation(models.Model):
    """
    Relations between Topics (see_also, related, etc.)
    """
    
    RELATION_TYPES = [
        ("SEE_ALSO", "See Also"),
        ("RELATED", "Related"),
        ("PARENT", "Parent Topic"),
        ("CHILD", "Child Topic"),
        ("ALIAS", "Alias"),
    ]
    
    source = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="incoming_relations")
    
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_relations"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "target", "relation_type"], 
                name="uniq_topic_relation"
            ),
        ]

    def __str__(self):
        return f"{self.source.slug} --{self.relation_type}--> {self.target.slug}"
```

---

## 🔌 Endpoints da API

### URLs: `bible/topics/urls.py`

```python
from django.urls import path
from . import views

app_name = "topics"

urlpatterns = [
    # Lista e Busca
    path("", views.TopicListView.as_view(), name="list"),
    path("search/", views.TopicSearchView.as_view(), name="search"),
    
    # Detalhe
    path("<slug:slug>/", views.TopicDetailView.as_view(), name="detail"),
    path("<slug:slug>/aspects/", views.TopicAspectsView.as_view(), name="aspects"),
    path("<slug:slug>/verses/", views.TopicVersesView.as_view(), name="verses"),
    path("<slug:slug>/themes/", views.TopicThemesView.as_view(), name="themes"),
    path("<slug:slug>/entities/", views.TopicEntitiesView.as_view(), name="entities"),
    path("<slug:slug>/symbols/", views.TopicSymbolsView.as_view(), name="symbols"),
    path("<slug:slug>/related/", views.TopicRelatedView.as_view(), name="related"),
    
    # Estatísticas e Análise
    path("<slug:slug>/statistics/", views.TopicStatisticsView.as_view(), name="statistics"),
    path("<slug:slug>/bible-coverage/", views.TopicBibleCoverageView.as_view(), name="bible-coverage"),
    
    # Navegação por letra
    path("by-letter/<str:letter>/", views.TopicsByLetterView.as_view(), name="by-letter"),
    
    # Entidades e Símbolos globais (canonical)
    path("entities/", views.EntityListView.as_view(), name="entities-list"),
    path("entities/<str:entity_type>/", views.EntitiesByTypeView.as_view(), name="entities-by-type"),
    path("symbols/", views.SymbolListView.as_view(), name="symbols-list"),
    path("symbols/<str:symbol_type>/", views.SymbolsByTypeView.as_view(), name="symbols-by-type"),
]
```

---

## 📝 Serializers: `bible/topics/serializers.py`

```python
"""Serializers for topics domain - i18n aware."""

from rest_framework import serializers

from ..models import (
    Topic, TopicName, TopicContent, TopicAspect,
    CanonicalEntity, CanonicalSymbol
)


class TopicSerializer(serializers.ModelSerializer):
    """
    Topic serializer with localized name and content.
    Follows BookSerializer pattern for i18n.
    """
    
    # Localized fields (resolved via get_language_from_context)
    name = serializers.SerializerMethodField()
    aliases = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    outline = serializers.SerializerMethodField()
    key_concepts = serializers.SerializerMethodField()
    theological_significance = serializers.SerializerMethodField()
    
    # Language of response
    language_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            "slug",
            "canonical_id",
            "name",
            "aliases",
            "summary",
            "outline",
            "key_concepts",
            "theological_significance",
            "total_verses",
            "ot_refs",
            "nt_refs",
            "books_count",
            "aspects_count",
            "ai_enriched",
            "ai_confidence",
            "primary_source",
            "available_sources",
            "language_code",
        ]
    
    def get_name(self, obj):
        """Get localized topic name."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        return obj.get_display_name(lang_code)
    
    def get_aliases(self, obj):
        """Get aliases in current language."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        name_obj = obj.names.filter(language__code=lang_code).first()
        if name_obj:
            return name_obj.aliases
        # Fallback
        name_obj = obj.names.filter(language__code="en").first()
        return name_obj.aliases if name_obj else []
    
    def get_summary(self, obj):
        """Get localized summary."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.summary
        # Fallback to English
        content = obj.contents.filter(language__code="en").first()
        return content.summary if content else ""
    
    def get_outline(self, obj):
        """Get localized outline."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.outline
        content = obj.contents.filter(language__code="en").first()
        return content.outline if content else []
    
    def get_key_concepts(self, obj):
        """Get localized key concepts."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.key_concepts
        content = obj.contents.filter(language__code="en").first()
        return content.key_concepts if content else []
    
    def get_theological_significance(self, obj):
        """Get localized theological significance."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.theological_significance
        content = obj.contents.filter(language__code="en").first()
        return content.theological_significance if content else ""
    
    def get_language_code(self, obj):
        """Return resolved language code."""
        from bible.utils.i18n import get_language_from_context
        return get_language_from_context(self.context)


class TopicAspectSerializer(serializers.ModelSerializer):
    """Aspect serializer with localized label."""
    
    label = serializers.SerializerMethodField()
    
    class Meta:
        model = TopicAspect
        fields = [
            "id",
            "label",
            "order",
            "verse_count",
            "ot_refs",
            "nt_refs",
            "books",
        ]
    
    def get_label(self, obj):
        """Get localized label."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        return obj.get_label(lang_code)


class EntitySerializer(serializers.ModelSerializer):
    """Canonical entity serializer with localized name."""
    
    display_name = serializers.SerializerMethodField()
    aliases = serializers.SerializerMethodField()
    
    class Meta:
        model = CanonicalEntity
        fields = [
            "canonical_id",
            "entity_type",
            "display_name",
            "aliases",
            "frequency",
        ]
    
    def get_display_name(self, obj):
        """Get localized display name."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        return obj.get_display_name(lang_code)
    
    def get_aliases(self, obj):
        """Get aliases in current language."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        name_obj = obj.names.filter(language__code=lang_code).first()
        return name_obj.aliases if name_obj else []


class SymbolSerializer(serializers.ModelSerializer):
    """Canonical symbol serializer with localized content."""
    
    display_name = serializers.SerializerMethodField()
    literal_meaning = serializers.SerializerMethodField()
    symbolic_meanings = serializers.SerializerMethodField()
    visual_correlations = serializers.SerializerMethodField()
    
    class Meta:
        model = CanonicalSymbol
        fields = [
            "canonical_id",
            "symbol_type",
            "display_name",
            "literal_meaning",
            "symbolic_meanings",
            "visual_correlations",
            "frequency",
        ]
    
    def get_display_name(self, obj):
        """Get localized display name."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.display_name
        content = obj.contents.filter(language__code="en").first()
        return content.display_name if content else obj.canonical_id.split(":")[-1]
    
    def get_literal_meaning(self, obj):
        """Get localized literal meaning."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.literal_meaning
        content = obj.contents.filter(language__code="en").first()
        return content.literal_meaning if content else ""
    
    def get_symbolic_meanings(self, obj):
        """Get localized symbolic meanings."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.symbolic_meanings
        content = obj.contents.filter(language__code="en").first()
        return content.symbolic_meanings if content else []
    
    def get_visual_correlations(self, obj):
        """Get localized visual correlations."""
        from bible.utils.i18n import get_language_from_context
        lang_code = get_language_from_context(self.context)
        content = obj.contents.filter(language__code=lang_code).first()
        if content:
            return content.visual_correlations
        content = obj.contents.filter(language__code="en").first()
        return content.visual_correlations if content else []
```

---

## 📋 Resumo dos Endpoints

Todos os endpoints suportam `?lang=` e `Accept-Language` header.

| Método | Endpoint | Descrição | i18n |
|--------|----------|-----------|------|
| GET | `/api/v1/topics/` | Lista paginada de tópicos | ✅ |
| GET | `/api/v1/topics/search/?q=` | Busca por nome/conteúdo | ✅ |
| GET | `/api/v1/topics/{slug}/` | Detalhe completo do tópico | ✅ |
| GET | `/api/v1/topics/{slug}/aspects/` | Aspectos/subtópicos | ✅ |
| GET | `/api/v1/topics/{slug}/verses/` | Versículos relacionados | ✅ |
| GET | `/api/v1/topics/{slug}/themes/` | Temas extraídos | ✅ |
| GET | `/api/v1/topics/{slug}/entities/` | Entidades mencionadas | ✅ |
| GET | `/api/v1/topics/{slug}/symbols/` | Símbolos bíblicos | ✅ |
| GET | `/api/v1/topics/{slug}/related/` | Tópicos relacionados | ✅ |
| GET | `/api/v1/topics/{slug}/statistics/` | Estatísticas completas | - |
| GET | `/api/v1/topics/{slug}/bible-coverage/` | Cobertura por livro/testamento | ✅ |
| GET | `/api/v1/topics/by-letter/{letter}/` | Tópicos por letra inicial | ✅ |
| GET | `/api/v1/topics/entities/` | Lista global de entidades | ✅ |
| GET | `/api/v1/topics/entities/{type}/` | Entidades por tipo | ✅ |
| GET | `/api/v1/topics/symbols/` | Lista global de símbolos | ✅ |

---

## 📦 Exemplo de Response

### GET `/api/v1/topics/abraham/?lang=pt`

```json
{
  "slug": "abraham",
  "canonical_id": "UNIFIED:abraham",
  "name": "Abraão",
  "aliases": ["Abrão"],
  "language_code": "pt",
  
  "summary": "Abraão é o patriarca fundador do povo de Israel, chamado por Deus para ser pai de muitas nações...",
  "outline": [
    "Chamado divino e jornada para Canaã",
    "Aliança com Deus e promessa de descendência",
    "Prova de fé com Isaque"
  ],
  "key_concepts": ["Fé", "Aliança", "Promessa", "Obediência"],
  "theological_significance": "Abraão é modelo de fé para judeus, cristãos e muçulmanos...",
  
  "statistics": {
    "total_verses": 156,
    "ot_refs": 120,
    "nt_refs": 36,
    "books_count": 11,
    "aspects_count": 25
  },
  
  "aspects_preview": [
    {"label": "Chamado divino de", "verse_count": 8},
    {"label": "Aliança de Deus com", "verse_count": 18},
    {"label": "Prova de fé", "verse_count": 5}
  ],
  
  "entities_preview": [
    {"name": "Sara", "type": "PERSON", "role": "Esposa de Abraão"},
    {"name": "Isaque", "type": "PERSON", "role": "Filho da promessa"},
    {"name": "Ur dos Caldeus", "type": "PLACE", "role": "Cidade de origem"}
  ],
  
  "symbols_preview": [
    {"name": "Altar", "type": "OBJECT", "meaning": "Adoração e sacrifício"},
    {"name": "Estrelas", "type": "NATURAL", "meaning": "Multidão de descendentes"}
  ],
  
  "related_topics": [
    {"slug": "isaac", "name": "Isaque", "relation": "SEE_ALSO"},
    {"slug": "faith", "name": "Fé", "relation": "RELATED"}
  ],
  
  "ai_enrichment": {
    "enriched": true,
    "model": "gpt-4o-mini",
    "confidence": 0.92,
    "enriched_at": "2025-12-01T20:30:00Z"
  },
  
  "sources": {
    "primary": "NAV",
    "available": ["NAV", "TOR"]
  }
}
```

### GET `/api/v1/topics/abraham/?lang=en`

```json
{
  "slug": "abraham",
  "canonical_id": "UNIFIED:abraham",
  "name": "Abraham",
  "aliases": ["Abram"],
  "language_code": "en",
  
  "summary": "Abraham is the founding patriarch of Israel, called by God to be the father of many nations...",
  "outline": [
    "Divine call and journey to Canaan",
    "God's covenant and promise of descendants",
    "Trial of faith with Isaac"
  ],
  "key_concepts": ["Faith", "Covenant", "Promise", "Obedience"],
  ...
}
```

---

## 🖥️ Uso no Frontend

### Página de Lista de Tópicos
```tsx
// GET /api/v1/topics/?page=1&letter=A
const { data } = useTopics({ letter: 'A', page: 1 });

// Renderiza lista alfabética com cards de tópicos
```

### Página de Detalhe do Tópico
```tsx
// GET /api/v1/topics/abraham/
const { topic } = useTopic('abraham');

// Mostra:
// - Summary e outline
// - Aspectos expandíveis
// - Versículos relacionados
// - Temas e entidades
// - Mapa de cobertura bíblica
```

### Busca de Tópicos
```tsx
// GET /api/v1/topics/search/?q=covenant
const { results } = useTopicSearch(query);

// Autocomplete com resultados
```

---

## 🔄 Migração de Dados

Script para importar os JSONs processados:

```bash
python manage.py import_topics data/topics/
```

---

## Próximos Passos

1. [ ] Criar models em `bible/models/topics.py`
2. [ ] Criar migrations
3. [ ] Criar serializers em `bible/topics/serializers.py`
4. [ ] Criar views em `bible/topics/views.py`
5. [ ] Criar script de importação
6. [ ] Adicionar testes
7. [ ] Documentar no OpenAPI
