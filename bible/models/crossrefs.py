from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Q

from .books import CanonicalBook


class CrossReference(models.Model):
    """
    Relação canônica e agnóstica à versão entre um trecho bíblico e outro.
    
    Enriquecido com:
    - Classificação do tipo de relação (citação, tipologia, profecia, etc.)
    - Análise teológica gerada por IA
    - Métricas de valor para estudo
    - Contexto literário e hermenêutico
    """

    # =========================================================================
    # RELATIONSHIP TYPE - Como os versículos se relacionam
    # =========================================================================
    class RelationType(models.TextChoices):
        # Citações e Alusões
        DIRECT_QUOTE = "direct_quote", "Direct Quote"        # Citação literal (NT citando AT)
        PARAPHRASE = "paraphrase", "Paraphrase"              # Citação parafraseada
        ALLUSION = "allusion", "Allusion"                    # Alusão/eco literário
        ECHO = "echo", "Echo"                                # Eco verbal sutil
        
        # Paralelos
        PARALLEL = "parallel", "Parallel Passage"            # Passagem paralela (Sinóticos)
        SYNOPTIC = "synoptic", "Synoptic Parallel"          # Paralelo sinótico específico
        DUPLICATE = "duplicate", "Duplicate Account"         # Mesmo evento (Reis/Crônicas)
        
        # Proféticos e Tipológicos
        PROPHECY_FULFILLMENT = "prophecy", "Prophecy-Fulfillment"  # Profecia → Cumprimento
        TYPOLOGY = "typology", "Typology"                    # Tipo → Antítipo
        FORESHADOW = "foreshadow", "Foreshadowing"           # Prenúncio narrativo
        
        # Temáticos e Conceituais
        THEMATIC = "thematic", "Thematic Connection"         # Tema em comum
        THEOLOGICAL = "theological", "Theological Link"      # Conexão doutrinária
        CONTRAST = "contrast", "Contrast"                    # Contraste intencional
        EXPANSION = "expansion", "Expansion"                 # Elaboração do conceito
        ILLUSTRATION = "illustration", "Illustration"        # Um ilustra o outro
        
        # Históricos
        HISTORICAL = "historical", "Historical Reference"    # Mesmo evento histórico
        GENEALOGICAL = "genealogical", "Genealogical"       # Conexão genealógica
        GEOGRAPHICAL = "geographical", "Geographical"        # Mesmo local
        
        # Linguísticos
        WORDPLAY = "wordplay", "Wordplay/Pun"               # Jogo de palavras
        INTERTEXTUAL = "intertextual", "Intertextual"       # Intertextualidade geral
        
        # Default
        UNCLASSIFIED = "unclassified", "Unclassified"       # Ainda não classificado

    class Direction(models.TextChoices):
        """Direção temporal/canônica da referência."""
        OT_TO_OT = "ot_ot", "Old Testament → Old Testament"
        OT_TO_NT = "ot_nt", "Old Testament → New Testament"
        NT_TO_OT = "nt_ot", "New Testament → Old Testament"
        NT_TO_NT = "nt_nt", "New Testament → New Testament"

    class Strength(models.TextChoices):
        """Força da conexão baseada em evidências."""
        CERTAIN = "certain", "Certain"           # Citação explícita, sem dúvida
        STRONG = "strong", "Strong"              # Altamente provável
        MODERATE = "moderate", "Moderate"        # Provável
        WEAK = "weak", "Weak"                    # Possível
        SPECULATIVE = "speculative", "Speculative"  # Especulativo

    class DifficultyLevel(models.TextChoices):
        """Nível de dificuldade para compreensão."""
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        SCHOLARLY = "scholarly", "Scholarly"

    # =========================================================================
    # CORE FIELDS - Identificação da referência
    # =========================================================================
    
    # De (versículo de origem)
    from_book = models.ForeignKey(
        CanonicalBook, 
        on_delete=models.CASCADE, 
        related_name="xrefs_from"
    )
    from_chapter = models.PositiveIntegerField()
    from_verse = models.PositiveIntegerField()

    # Para (versículo de destino, com suporte a intervalo)
    to_book = models.ForeignKey(
        CanonicalBook, 
        on_delete=models.CASCADE, 
        related_name="xrefs_to"
    )
    to_chapter = models.PositiveIntegerField()
    to_verse_start = models.PositiveIntegerField()
    to_verse_end = models.PositiveIntegerField()

    # =========================================================================
    # CLASSIFICATION - Tipo e natureza da relação
    # =========================================================================
    
    relation_type = models.CharField(
        max_length=30,
        choices=RelationType.choices,
        default=RelationType.UNCLASSIFIED,
        db_index=True,
        help_text="Tipo de relação entre os versículos"
    )
    
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        blank=True,
        db_index=True,
        help_text="Direção canônica (AT→NT, NT→AT, etc.)"
    )
    
    strength = models.CharField(
        max_length=15,
        choices=Strength.choices,
        default=Strength.MODERATE,
        help_text="Força/certeza da conexão"
    )

    # =========================================================================
    # SOURCE & CONFIDENCE - Origem e confiabilidade
    # =========================================================================
    
    source = models.CharField(
        max_length=120, 
        blank=True, 
        default="",
        db_index=True,
        help_text="Fonte: TSK, OpenBible, Nestle-Aland, etc."
    )
    
    votes = models.PositiveIntegerField(
        default=0, 
        help_text="Votos de relevância (crowdsourced)"
    )
    
    confidence = models.FloatField(
        default=1.0, 
        help_text="Confiança na referência (0.0 a 1.0)"
    )

    # =========================================================================
    # AI ENRICHMENT - Campos gerados por IA 🤖
    # =========================================================================
    
    # Explicações
    explanation = models.TextField(
        blank=True, 
        default="",
        help_text="Explicação da referência (fonte original ou curada)"
    )
    
    ai_explanation = models.TextField(
        blank=True,
        help_text="Explicação detalhada gerada por IA (inglês)"
    )
    
    ai_explanation_pt = models.TextField(
        blank=True,
        help_text="Explicação detalhada gerada por IA (português)"
    )
    
    # Análise Teológica
    theological_significance = models.TextField(
        blank=True,
        help_text="Significado teológico desta conexão"
    )
    
    shared_themes = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Temas compartilhados: ['redemption', 'covenant', 'faith']"
    )
    
    shared_keywords_hebrew = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Palavras-chave hebraicas em comum"
    )
    
    shared_keywords_greek = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Palavras-chave gregas em comum"
    )
    
    # Contexto Hermenêutico
    hermeneutical_notes = models.TextField(
        blank=True,
        help_text="Notas sobre princípios hermenêuticos aplicáveis"
    )

    # =========================================================================
    # STUDY METRICS - Valor para estudo
    # =========================================================================
    
    study_value = models.FloatField(
        default=0.0,
        help_text="Valor para estudo bíblico (0-10)"
    )
    
    difficulty_level = models.CharField(
        max_length=15,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.INTERMEDIATE,
        help_text="Nível de dificuldade para compreensão"
    )
    
    discovery_potential = models.FloatField(
        default=0.0,
        help_text="Quão 'surpreendente' ou insight-geradora é esta conexão (0-10)"
    )
    
    # Similaridade linguística/semântica
    linguistic_similarity = models.FloatField(
        default=0.0,
        help_text="Similaridade textual calculada (0-1)"
    )
    
    semantic_similarity = models.FloatField(
        default=0.0,
        help_text="Similaridade semântica via embeddings (0-1)"
    )

    # =========================================================================
    # LITERARY CONTEXT - Contexto literário
    # =========================================================================
    
    class LiteraryGenre(models.TextChoices):
        NARRATIVE = "narrative", "Narrative"
        LAW = "law", "Law/Torah"
        POETRY = "poetry", "Poetry"
        WISDOM = "wisdom", "Wisdom Literature"
        PROPHECY = "prophecy", "Prophecy"
        APOCALYPTIC = "apocalyptic", "Apocalyptic"
        GOSPEL = "gospel", "Gospel"
        EPISTLE = "epistle", "Epistle"
        PARABLE = "parable", "Parable"
        PSALM = "psalm", "Psalm"
        PROVERB = "proverb", "Proverb"
    
    genre_from = models.CharField(
        max_length=20,
        choices=LiteraryGenre.choices,
        blank=True,
        help_text="Gênero literário do versículo de origem"
    )
    
    genre_to = models.CharField(
        max_length=20,
        choices=LiteraryGenre.choices,
        blank=True,
        help_text="Gênero literário do versículo de destino"
    )
    
    same_author = models.BooleanField(
        default=False,
        help_text="Mesmo autor tradicional (Paulo→Paulo, Moisés→Moisés)"
    )

    # =========================================================================
    # AI PROCESSING METADATA
    # =========================================================================
    
    ai_enriched = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Se foi enriquecido por IA"
    )
    
    ai_model = models.CharField(
        max_length=50,
        blank=True,
        help_text="Modelo usado para enriquecimento"
    )
    
    ai_enriched_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando foi enriquecido por IA"
    )
    
    ai_run_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="ID do batch de processamento AI"
    )

    # =========================================================================
    # ENGAGEMENT METRICS (futuro)
    # =========================================================================
    
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Número de visualizações"
    )
    
    bookmark_count = models.PositiveIntegerField(
        default=0,
        help_text="Número de vezes que foi salvo/favoritado"
    )

    # =========================================================================
    # TIMESTAMPS
    # =========================================================================
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = "cross_references"
        ordering = ["from_book", "from_chapter", "from_verse"]
        indexes = [
            # Core lookups
            models.Index(
                fields=["from_book", "from_chapter", "from_verse"], 
                name="cr_from_idx"
            ),
            models.Index(
                fields=["to_book", "to_chapter", "to_verse_start"], 
                name="cr_to_idx"
            ),
            # Classification lookups
            models.Index(fields=["relation_type"], name="cr_relation_type_idx"),
            models.Index(fields=["direction"], name="cr_direction_idx"),
            models.Index(fields=["strength"], name="cr_strength_idx"),
            # AI enrichment
            models.Index(fields=["ai_enriched"], name="cr_ai_enriched_idx"),
            # Study value
            models.Index(fields=["study_value"], name="cr_study_value_idx"),
            models.Index(fields=["difficulty_level"], name="cr_difficulty_idx"),
            # Combined for common queries
            models.Index(
                fields=["relation_type", "ai_enriched"],
                name="cr_type_enriched_idx"
            ),
        ]
        constraints = [
            # Garante unicidade da referência por fonte
            models.UniqueConstraint(
                fields=[
                    "from_book",
                    "from_chapter",
                    "from_verse",
                    "to_book",
                    "to_chapter",
                    "to_verse_start",
                    "to_verse_end",
                    "source",
                ],
                name="uniq_crossref_full",
            ),
            # Garante intervalo válido
            models.CheckConstraint(
                check=Q(to_verse_end__gte=F("to_verse_start")), 
                name="cr_to_end_gte_start"
            ),
            # Garante confiança no intervalo correto
            models.CheckConstraint(
                check=Q(confidence__gte=0.0) & Q(confidence__lte=1.0), 
                name="cr_confidence_0_1"
            ),
            # Garante study_value no intervalo correto
            models.CheckConstraint(
                check=Q(study_value__gte=0.0) & Q(study_value__lte=10.0),
                name="cr_study_value_0_10"
            ),
        ]

    def __str__(self):
        to_range = f"{self.to_verse_start}"
        if self.to_verse_end > self.to_verse_start:
            to_range += f"-{self.to_verse_end}"

        return (
            f"{self.from_book.osis_code} {self.from_chapter}:{self.from_verse} → "
            f"{self.to_book.osis_code} {self.to_chapter}:{to_range}"
        )

    @property
    def from_reference(self) -> str:
        """Referência de origem formatada."""
        return f"{self.from_book.osis_code} {self.from_chapter}:{self.from_verse}"

    @property
    def to_reference(self) -> str:
        """Referência de destino formatada."""
        to_range = f"{self.to_verse_start}"
        if self.to_verse_end > self.to_verse_start:
            to_range += f"-{self.to_verse_end}"
        return f"{self.to_book.osis_code} {self.to_chapter}:{to_range}"

    def set_direction_from_books(self):
        """Define a direção baseada nos testamentos dos livros."""
        from_ot = self.from_book.testament == "OT"
        to_ot = self.to_book.testament == "OT"
        
        if from_ot and to_ot:
            self.direction = self.Direction.OT_TO_OT
        elif from_ot and not to_ot:
            self.direction = self.Direction.OT_TO_NT
        elif not from_ot and to_ot:
            self.direction = self.Direction.NT_TO_OT
        else:
            self.direction = self.Direction.NT_TO_NT
