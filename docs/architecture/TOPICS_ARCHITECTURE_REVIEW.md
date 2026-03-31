# 📚 Topics Architecture Review - Análise e Melhorias

> **Objetivo**: Criar a melhor API do mundo para estudo bíblico seguindo Clean Code, SOLID e boas práticas REST.

## 📊 1. Análise Comparativa: JSON Pipeline vs Modelos Propostos

### 1.1 Estrutura Atual do JSON (topics_v3)

```json
{
  "topic": "ABRAHAM",
  "slug": "abraham",
  "type": "topic",
  
  "reference_groups": [
    {
      "name": "Divine call of",
      "references": ["Gn 12:1", "Gn 12:4", "Ne 9:7", "Is 51:2", "At 7:2-3", "Hb 11:8"]
    }
  ],
  
  "biblical_references": [
    {
      "book": "Genesis",
      "book_abbrev": "gen",
      "chapter": 12,
      "testament": "OT",
      "verses": [1, 4],
      "verse_count": 2
    }
  ],
  
  "ai_enrichment": {
    "summary": "...",
    "outline": ["..."],
    "key_concepts": ["Fé", "Promessa", "Aliança"],
    "theological_significance": "...",
    "model": "gpt-4o-mini",
    "run_id": "enr_20251203_230600_72ad0883",
    "confidence": 1.0,
    "generated_at": "2025-12-03T23:06:00.850560"
  },
  
  "ai_themes_normalized": [
    {
      "theme_id": null,
      "proposal_id": "prop:faith_and_obedience_05f904",
      "label_original": "Fé e obediência de Abraão",
      "label_en": "Faith and Obedience",
      "label_normalized": "faith_and_obedience",
      "anchor_verses": ["Gênesis 12:1", "Hebreus 11:8"],
      "relevance_score": 9,
      "semantic_keywords": ["faith", "obedience", "trust"],
      "theological_domain": "soteriology",
      "parent_theme": null,
      "aspect": "A disposição de Abraão em seguir a direção de Deus",
      "source": "ai_enrichment",
      "anchor_source": "ai_trusted",
      "anchor_meta": {
        "ai_suggested": 2,
        "validated": 0,
        "fallback_used": false
      }
    }
  ],
  
  "phase1_discovery": {
    "processed_at": "...",
    "summary": {...},
    "results": [...]
  },
  
  "entity_links": [
    {
      "canonical_id": "PER:abraham",
      "namespace": "PERSON",
      "role": "primary",
      "confidence": 0.9,
      "source": "topic_resolver",
      "status": "proposed",
      "provenance": {...}
    }
  ],
  
  "definitions": [
    {
      "source": "EAS",
      "text": "Father of a multitude...",
      "extracted_refs": [...]
    }
  ],
  
  "cross_reference_network": {
    "1 Corinthians 6:7": [
      {"to_verse": "1PE.3.9", "score": 7, "votes": 5, "strength": "weak"}
    ]
  },
  
  "see_also": [],
  "aliases": [],
  "stats": {
    "entries_count": 42,
    "ot_refs": 9,
    "nt_refs": 21,
    "total_verses": 30
  }
}
```

### 1.2 Gap Analysis: Campos Faltantes no Modelo

| Campo JSON | Modelo Proposto | Status |
|------------|-----------------|--------|
| `topic` | `canonical_name` | ✅ OK |
| `slug` | `slug` | ✅ OK |
| `type` | ❌ Falta | 🔴 Adicionar |
| `reference_groups` | `TopicAspect` | ⚠️ Parcial |
| `reference_groups[].references` | ❌ Falta | 🔴 Mapeamento perdido |
| `biblical_references` | ❌ Derivado | ⚠️ Recalcular |
| `ai_enrichment.run_id` | ❌ Falta | 🔴 Rastreabilidade |
| `ai_enrichment.generated_at` | `ai_enriched_at` | ✅ OK |
| `ai_themes_normalized` | `TopicTheme` | ⚠️ Muito simplificado |
| `ai_themes_normalized[].anchor_verses` | ❌ Falta | 🔴 CRÍTICO |
| `ai_themes_normalized[].semantic_keywords` | ❌ Falta | 🔴 Busca semântica |
| `ai_themes_normalized[].theological_domain` | ❌ Falta | 🔴 Classificação |
| `ai_themes_normalized[].anchor_meta` | ❌ Falta | 🟡 Auditoria |
| `phase1_discovery` | ❌ Falta | 🟡 Pipeline metadata |
| `definitions` | ❌ Falta | 🔴 CRÍTICO |
| `definitions[].source` | ❌ Falta | 🔴 EAS, SMI, NAV |
| `cross_reference_network` | ❌ Falta | 🔴 Rede TSK |
| `entity_links[].provenance` | ❌ Falta | 🟡 Rastreabilidade |
| `stats` | Campos separados | ⚠️ OK |

---

## 🏗️ 2. Propostas de Melhorias nos Modelos

### 2.1 Modelo `Topic` - Campos Adicionais

```python
class Topic(models.Model):
    """
    Biblical topic/encyclopedia entry.
    
    Follows Domain-Driven Design principles:
    - Canonical entry is language-agnostic
    - All localized content in separate models
    - Clear separation between source data and AI enrichment
    """
    
    # === Identificação ===
    slug = models.SlugField(max_length=150, unique=True, db_index=True)
    canonical_id = models.CharField(max_length=100, unique=True)  # "UNIFIED:abraham"
    canonical_name = models.CharField(max_length=200)  # "ABRAHAM"
    name_normalized = models.CharField(max_length=200, db_index=True)  # "abraham"
    
    # 🆕 NOVO: Tipo de tópico para classificação
    class TopicType(models.TextChoices):
        PERSON = "person", "Person"
        PLACE = "place", "Place"
        CONCEPT = "concept", "Concept"
        EVENT = "event", "Event"
        OBJECT = "object", "Object"
        LITERARY = "literary", "Literary Term"
    
    topic_type = models.CharField(
        max_length=20,
        choices=TopicType.choices,
        default=TopicType.CONCEPT,
        db_index=True
    )
    
    # === Fontes ===
    primary_source = models.CharField(max_length=10)  # "NAV", "TOR"
    available_sources = ArrayField(models.CharField(max_length=10), default=list)
    
    # === Estatísticas ===
    total_verses = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)
    books_count = models.IntegerField(default=0)
    aspects_count = models.IntegerField(default=0)
    
    # 🆕 NOVO: Estatísticas de engajamento
    view_count = models.IntegerField(default=0)  # Para analytics/ranking
    
    # === AI Enrichment ===
    ai_enriched = models.BooleanField(default=False)
    ai_model = models.CharField(max_length=50, blank=True)
    ai_confidence = models.FloatField(default=0.0)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    
    # 🆕 NOVO: Rastreabilidade do AI
    ai_run_id = models.CharField(max_length=100, blank=True, db_index=True)  # "enr_20251203_..."
    
    # === Qualidade ===
    quality_score = models.FloatField(default=0.0)
    
    # 🆕 NOVO: Flags de revisão
    needs_review = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)
    
    # === Timestamps ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topics"
        ordering = ["name_normalized"]
        indexes = [
            models.Index(fields=["name_normalized"]),
            models.Index(fields=["primary_source"]),
            models.Index(fields=["ai_enriched"]),
            models.Index(fields=["topic_type"]),  # 🆕 NOVO
            models.Index(fields=["quality_score"]),  # 🆕 NOVO
            # 🆕 NOVO: Índice composto para buscas comuns
            models.Index(
                fields=["topic_type", "ai_enriched"],
                name="topic_type_enriched_idx"
            ),
        ]
```

### 2.2 🆕 NOVO: Modelo `TopicDefinition` - Definições de Dicionários

```python
class TopicDefinition(models.Model):
    """
    Dictionary definitions for a Topic from different sources.
    
    Sources:
    - EAS: Easton's Bible Dictionary
    - SMI: Smith's Bible Dictionary
    - NAV: Nave's Topical Bible (index entries)
    - TOR: Torrey's Topical Textbook
    """
    
    class SourceType(models.TextChoices):
        EAS = "EAS", "Easton's Bible Dictionary"
        SMI = "SMI", "Smith's Bible Dictionary"
        NAV = "NAV", "Nave's Topical Bible"
        TOR = "TOR", "Torrey's Topical Textbook"
        ATS = "ATS", "American Tract Society Dictionary"
        ISB = "ISB", "International Standard Bible Encyclopedia"
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="definitions")
    
    source = models.CharField(max_length=3, choices=SourceType.choices, db_index=True)
    
    # Conteúdo bruto do dicionário (language-agnostic, geralmente em inglês)
    text = models.TextField()
    text_length = models.IntegerField(default=0)  # Para ordenação/paginação
    
    # Referências extraídas automaticamente do texto
    extracted_refs = models.JSONField(default=list)  # Array of {book, chapter, verses, ...}
    refs_count = models.IntegerField(default=0)
    
    # Metadados de processamento
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_definitions"
        ordering = ["topic", "source"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "source"],
                name="uniq_topic_definition_source"
            ),
        ]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["refs_count"]),
        ]

    def __str__(self):
        return f"{self.topic.slug} ({self.source})"
    
    def save(self, *args, **kwargs):
        self.text_length = len(self.text)
        self.refs_count = len(self.extracted_refs) if self.extracted_refs else 0
        super().save(*args, **kwargs)
```

### 2.3 Modelo `TopicAspect` - Melhorado com Referências

```python
class TopicAspect(models.Model):
    """
    Structured aspect/subtopic within a Topic.
    
    Maps to `reference_groups` from JSON:
    - "Divine call of" → aspect with references [Gn 12:1, Hb 11:8, ...]
    """
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="aspects")
    
    # Canonical label (English)
    canonical_label = models.CharField(max_length=500)
    
    # 🆕 NOVO: Slug para URLs amigáveis
    slug = models.SlugField(max_length=150, blank=True)
    
    order = models.IntegerField(default=0)
    
    # 🆕 NOVO: Referências brutas (preserva formato original)
    # Ex: ["Gn 12:1", "Hb 11:8"] - do JSON original
    raw_references = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True
    )
    
    # Estatísticas do aspecto
    verse_count = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)
    
    # Livros onde aparece (OSIS codes)
    books = ArrayField(models.CharField(max_length=20), default=list)
    
    # 🆕 NOVO: Fonte do aspecto
    source = models.CharField(max_length=10, default="NAV")  # NAV, TOR, AI

    class Meta:
        db_table = "topic_aspects"
        ordering = ["topic", "order"]
        indexes = [
            models.Index(fields=["topic", "order"]),
            models.Index(fields=["slug"]),  # 🆕 NOVO
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.canonical_label[:100])
        super().save(*args, **kwargs)
```

### 2.4 🆕 NOVO: Modelo `TopicThemeLink` - Temas com Metadados Completos

O modelo `TopicTheme` proposto é muito simplificado. Precisamos capturar todos os campos de `ai_themes_normalized`:

```python
class TopicThemeLink(models.Model):
    """
    AI-extracted themes for a Topic with full metadata.
    
    Maps to `ai_themes_normalized[]` from JSON.
    This is a rich link table with analysis results.
    """
    
    class TheologicalDomain(models.TextChoices):
        THEOLOGY_PROPER = "theology_proper", "Theology Proper (God)"
        CHRISTOLOGY = "christology", "Christology (Christ)"
        PNEUMATOLOGY = "pneumatology", "Pneumatology (Holy Spirit)"
        ANTHROPOLOGY = "anthropology", "Anthropology (Humanity)"
        HAMARTIOLOGY = "hamartiology", "Hamartiology (Sin)"
        SOTERIOLOGY = "soteriology", "Soteriology (Salvation)"
        ECCLESIOLOGY = "ecclesiology", "Ecclesiology (Church)"
        ESCHATOLOGY = "eschatology", "Eschatology (End Times)"
        BIBLIOLOGY = "bibliology", "Bibliology (Scripture)"
        ANGELOLOGY = "angelology", "Angelology (Angels/Demons)"
        ETHICS = "ethics", "Ethics/Morality"
        WORSHIP = "worship", "Worship/Liturgy"
    
    class AnchorSource(models.TextChoices):
        AI_TRUSTED = "ai_trusted", "AI Trusted"
        AI_FALLBACK = "ai_fallback", "AI Fallback"
        MANUAL = "manual", "Manual/Curated"
        DERIVED = "derived", "Derived from Data"
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="theme_links")
    theme = models.ForeignKey("Theme", on_delete=models.CASCADE, related_name="topic_sources")
    
    # === Identificação do Tema ===
    # Preservamos proposal_id para rastreabilidade
    proposal_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Labels multilingue
    label_original = models.CharField(max_length=300)  # "Fé e obediência de Abraão"
    label_en = models.CharField(max_length=300)  # "Faith and Obedience"
    label_normalized = models.CharField(max_length=200, db_index=True)  # "faith_and_obedience"
    
    # === Anchor Verses (CRÍTICO) ===
    anchor_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Key verses that anchor this theme, e.g., ['Genesis 12:1', 'Hebrews 11:8']"
    )
    anchor_source = models.CharField(
        max_length=20,
        choices=AnchorSource.choices,
        default=AnchorSource.AI_TRUSTED
    )
    anchor_meta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about anchor selection: ai_suggested, validated, fallback_used"
    )
    
    # === Análise Semântica ===
    semantic_keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Keywords for semantic search: ['faith', 'obedience', 'trust']"
    )
    
    # === Classificação Teológica ===
    theological_domain = models.CharField(
        max_length=30,
        choices=TheologicalDomain.choices,
        blank=True
    )
    
    # === Hierarquia de Temas ===
    parent_theme = models.ForeignKey(
        "Theme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_topic_links"
    )
    
    # === Contexto ===
    aspect = models.TextField(blank=True)  # "A disposição de Abraão em seguir..."
    
    # === Métricas ===
    relevance_score = models.FloatField(default=0.0)  # 0-10
    confidence = models.FloatField(default=1.0)
    
    # === Proveniência ===
    source = models.CharField(max_length=20, default="ai_enrichment")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_theme_links"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "theme"],
                name="uniq_topic_theme_link"
            ),
        ]
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["theme"]),
            models.Index(fields=["label_normalized"]),
            models.Index(fields=["theological_domain"]),
            models.Index(fields=["relevance_score"]),
            GinIndex(fields=["semantic_keywords"], name="topictheme_keywords_gin"),
            GinIndex(fields=["anchor_verses"], name="topictheme_anchors_gin"),
        ]
```

### 2.5 🆕 NOVO: Modelo `TopicCrossReference` - Rede de Referências Cruzadas

```python
class TopicCrossReference(models.Model):
    """
    Cross-reference network for a Topic.
    
    Maps to `cross_reference_network` from JSON (TSK data).
    Stores relationships between verses within the topic context.
    """
    
    class Strength(models.TextChoices):
        STRONG = "strong", "Strong"
        MODERATE = "moderate", "Moderate"
        WEAK = "weak", "Weak"
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="cross_references")
    
    # Source verse (human-readable format stored, normalized to verse FK if possible)
    from_verse_ref = models.CharField(max_length=100, db_index=True)  # "1 Corinthians 6:7"
    from_verse = models.ForeignKey(
        "Verse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="topic_xrefs_out"
    )
    
    # Target verse (OSIS format)
    to_verse_ref = models.CharField(max_length=100, db_index=True)  # "1PE.3.9"
    to_verse = models.ForeignKey(
        "Verse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="topic_xrefs_in"
    )
    
    # Relationship strength (from TSK)
    score = models.IntegerField(default=0)  # 0-10
    votes = models.IntegerField(default=0)  # Consensus count
    strength = models.CharField(
        max_length=10,
        choices=Strength.choices,
        default=Strength.WEAK
    )

    class Meta:
        db_table = "topic_cross_references"
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["from_verse_ref"]),
            models.Index(fields=["to_verse_ref"]),
            models.Index(fields=["strength"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "from_verse_ref", "to_verse_ref"],
                name="uniq_topic_xref"
            ),
        ]
```

### 2.6 🆕 NOVO: Modelo `TopicPipelineMetadata` - Rastreabilidade do Pipeline

```python
class TopicPipelineMetadata(models.Model):
    """
    Pipeline processing metadata for a Topic.
    
    Stores `phase1_discovery` and other pipeline artifacts for:
    - Auditoria de processamento
    - Reprodutibilidade
    - Debug de problemas
    """
    
    topic = models.OneToOneField(
        Topic,
        on_delete=models.CASCADE,
        related_name="pipeline_metadata"
    )
    
    # Phase 0: Initial processing
    phase0_processed_at = models.DateTimeField(null=True, blank=True)
    phase0_run_id = models.CharField(max_length=100, blank=True)
    
    # Phase 1: Theme discovery
    phase1_processed_at = models.DateTimeField(null=True, blank=True)
    phase1_summary = models.JSONField(default=dict, blank=True)
    phase1_results = models.JSONField(default=list, blank=True)
    
    # Phase 2: Entity resolution (futuro)
    phase2_processed_at = models.DateTimeField(null=True, blank=True)
    
    # Full JSON backup (comprimido)
    raw_json_backup = models.BinaryField(null=True, blank=True)  # gzip compressed
    
    # Versão do pipeline
    pipeline_version = models.CharField(max_length=20, default="1.0")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_pipeline_metadata"
```

---

## 🔌 3. Propostas de Melhorias na API

### 3.1 Novos Endpoints

| Método | Endpoint | Descrição | Justificativa |
|--------|----------|-----------|---------------|
| GET | `/api/v1/topics/{slug}/definitions/` | Definições de dicionários | 🆕 EAS, SMI, NAV |
| GET | `/api/v1/topics/{slug}/cross-references/` | Rede de refs cruzadas | 🆕 TSK network |
| GET | `/api/v1/topics/{slug}/anchor-verses/` | Versículos âncora dos temas | 🆕 Quick access |
| GET | `/api/v1/topics/by-type/{type}/` | Tópicos por tipo | 🆕 person, place, concept |
| GET | `/api/v1/topics/{slug}/timeline/` | Timeline de eventos | 🆕 Para persons/events |
| POST | `/api/v1/topics/{slug}/report/` | Reportar erro | 🆕 Crowdsource quality |

### 3.2 Endpoint Melhorado: `/api/v1/topics/{slug}/`

```python
# Response aprimorado
{
  "slug": "abraham",
  "canonical_id": "UNIFIED:abraham",
  "topic_type": "person",  # 🆕
  "name": "Abraão",
  "aliases": ["Abrão"],
  
  "definitions": {  # 🆕 Preview das definições
    "eas": {
      "excerpt": "Father of a multitude, son of Terah...",
      "refs_count": 45
    },
    "smi": {
      "excerpt": "...",
      "refs_count": 32
    }
  },
  
  "themes": [  # 🆕 Temas com anchor_verses
    {
      "label": "Fé e obediência",
      "anchor_verses": ["Gênesis 12:1", "Hebreus 11:8"],
      "theological_domain": "soteriology",
      "relevance_score": 9
    }
  ],
  
  "cross_references_count": 156,  # 🆕
  
  "ai_metadata": {  # 🆕 Expandido
    "enriched": true,
    "model": "gpt-4o-mini",
    "confidence": 0.92,
    "run_id": "enr_20251203_230600_72ad0883",
    "enriched_at": "2025-12-03T23:06:00Z"
  },
  
  "pipeline_info": {  # 🆕 Opcional, para admins
    "phase1_status": "completed",
    "themes_proposed": 3,
    "themes_approved": 2
  }
}
```

### 3.3 Serializer Otimizado com Prefetch

```python
class TopicDetailSerializer(serializers.ModelSerializer):
    """
    Optimized serializer with prefetch hints.
    
    Use with:
    Topic.objects.select_related(
        'pipeline_metadata'
    ).prefetch_related(
        'names',
        'contents',
        'definitions',
        'aspects__labels',
        Prefetch('theme_links', queryset=TopicThemeLink.objects.select_related('theme'))
    )
    """
    
    # ... campos
```

---

## 🎯 4. Princípios SOLID Aplicados

### 4.1 Single Responsibility Principle (SRP)

- ✅ `Topic` = Entidade canônica apenas
- ✅ `TopicName` = Nomes por idioma
- ✅ `TopicContent` = Conteúdo localizado
- ✅ `TopicDefinition` = Definições de dicionários
- ✅ `TopicThemeLink` = Relação tema-tópico com metadados

### 4.2 Open/Closed Principle (OCP)

```python
# Novo tipo de fonte? Apenas adicione à enum
class SourceType(models.TextChoices):
    EAS = "EAS", "Easton's"
    SMI = "SMI", "Smith's"
    ISB = "ISB", "ISBE"  # 🆕 Fácil de adicionar
```

### 4.3 Liskov Substitution Principle (LSP)

- Todos os serializers seguem interface consistente
- `get_display_name(language_code)` funciona igual em todas entidades

### 4.4 Interface Segregation Principle (ISP)

```python
# Serializers separados para diferentes casos de uso
class TopicListSerializer(...)    # Lista: campos mínimos
class TopicDetailSerializer(...)  # Detalhe: campos completos
class TopicSearchSerializer(...)  # Busca: highlight + score
```

### 4.5 Dependency Inversion Principle (DIP)

```python
# Views dependem de abstrações (services), não de implementações diretas
class TopicDetailView(APIView):
    def get(self, request, slug):
        # Serviço injeta lógica de negócio
        topic = TopicService.get_with_localization(slug, request)
        return Response(TopicDetailSerializer(topic, context={'request': request}).data)
```

---

## 🚀 5. Checklist de Implementação

### 5.1 Models (Prioridade Alta)

- [ ] Adicionar `topic_type` em `Topic`
- [ ] Adicionar `ai_run_id` em `Topic`
- [ ] Criar `TopicDefinition` model
- [ ] Renomear `TopicTheme` → `TopicThemeLink` com campos expandidos
- [ ] Adicionar `raw_references` em `TopicAspect`
- [ ] Criar `TopicCrossReference` model
- [ ] Criar `TopicPipelineMetadata` model

### 5.2 Migrations

```bash
python manage.py makemigrations bible
python manage.py migrate
```

### 5.3 Serializers

- [ ] Criar `TopicDefinitionSerializer`
- [ ] Expandir `TopicThemeLinkSerializer` com anchor_verses
- [ ] Criar `TopicCrossReferenceSerializer`
- [ ] Otimizar `TopicDetailSerializer` com prefetch

### 5.4 Views

- [ ] `TopicDefinitionsView`
- [ ] `TopicCrossReferencesView`
- [ ] `TopicsByTypeView`
- [ ] Endpoint de report

### 5.5 Script de Importação

- [ ] Atualizar `import_topics.py` para novos models
- [ ] Mapear `definitions[]` → `TopicDefinition`
- [ ] Mapear `ai_themes_normalized[]` → `TopicThemeLink`
- [ ] Mapear `cross_reference_network` → `TopicCrossReference`

### 5.6 Testes

- [ ] Unit tests para cada model
- [ ] API tests para cada endpoint
- [ ] Test fixtures com dados realistas

---

## 📈 6. Métricas de Sucesso

| Métrica | Alvo |
|---------|------|
| Cobertura de testes | ≥ 85% |
| Tempo de resposta (p95) | < 200ms |
| N+1 queries | 0 |
| Endpoints documentados | 100% |
| i18n coverage | pt, en, es |

---

## 📝 7. Próximos Passos Recomendados

1. **Revisar esta proposta** com o time
2. **Priorizar features** por valor de negócio
3. **Criar models incrementalmente** (evitar Big Bang)
4. **TDD**: Escrever testes antes da implementação
5. **Documentar** cada endpoint no OpenAPI

---

*Documento criado em: 2025-01-XX*
*Autor: Bible API Architecture Review*
