

# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

    # APIs v1
    path("api/v1/bible/", include(("bible.urls", "bible"), namespace="bible")),
    path("api/v1/ai/", include(("bible.ai.urls", "ai"), namespace="ai")),
    path("api/v1/bible/audio/", include(("bible.apps.audio.urls", "audio"), namespace="audio")),
    path("api/v1/bible/resources/", include(("bible.apps.resources.urls", "resources"), namespace="resources")),

    # ✅ Schema agregado da v1
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="v1_schema"),
    path("api/v1/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="v1_schema"), name="v1_swagger_ui"),
    path("api/v1/schema/redoc/", SpectacularRedocView.as_view(url_name="v1_schema"), name="v1_redoc"),
]


from django.urls import path, include
from . import views

app_name = "bible"

urlpatterns = [
    # 📊 Raiz / visão geral
    path("overview/", views.BibleOverview.as_view(), name="overview"),

    # 📚 BOOKS
    path("books/", include([
        path("", views.BookSearchView.as_view(), name="books_list"),
        path("by-author/<str:author_name>/", views.BooksByAuthorView.as_view(), name="books_by_author"),
        path("by-testament/<int:testament_id>/", views.BooksByTestamentView.as_view(), name="books_by_testament"),
        path("<str:book_name>/chapters/", views.ChaptersByBookView.as_view(), name="book_chapters"),
        path("<str:book_name>/info/", views.BookInfoView.as_view(), name="book_info"),
        path("<str:book_name>/outline/", views.BookOutlineView.as_view(), name="book_outline"),
        path("<str:book_name>/context/", views.BookContextView.as_view(), name="book_context"),
        path("<str:book_name>/structure/", views.BookStructureView.as_view(), name="book_structure"),
        path("<str:book_name>/statistics/", views.BookStatisticsView.as_view(), name="book_statistics"),
    ])),

    # 🏷️ THEMES
    path("themes/", include([
        path("", views.ThemeListView.as_view(), name="themes_list"),
        path("search/", views.ThemeSearchView.as_view(), name="themes_search"),
        path("<int:theme_id>/detail/", views.ThemeDetailView.as_view(), name="theme_detail"),
        path("<int:theme_id>/statistics/", views.ThemeStatisticsView.as_view(), name="theme_statistics"),
        path("analysis/by-book/<str:book_name>/", views.ThemeAnalysisByBookView.as_view(), name="theme_analysis_book"),
        path("<int:theme_id>/progression/", views.ThemeProgressionView.as_view(), name="theme_progression"),
        path("concept-map/<str:concept>/", views.ConceptMapView.as_view(), name="concept_map"),
    ])),

    # 📜 VERSES
    path("verses/", include([
        path("", views.VerseListView.as_view(), name="verses_list"),
        path("search/", views.VerseSearchView.as_view(), name="verses_search"),
        path("by-book/<str:book_name>/", views.VersesByBookView.as_view(), name="verses_by_book"),
        path("by-chapter/<str:book_name>/<int:chapter>/", views.VersesByChapterView.as_view(), name="verses_by_chapter"),
        path("by-theme/<int:theme_id>/", views.VersesByThemeView.as_view(), name="verses_by_theme"),
        path("comparison/<str:book_name>/<int:chapter>/<int:verse>/", views.VerseComparisonView.as_view(), name="verse_comparison"),
        path("<int:verse_id>/info/", views.VerseInfoView.as_view(), name="verse_info"),
        path("<int:verse_id>/context/", views.VerseContextView.as_view(), name="verse_context"),
        path("<int:verse_id>/comments/", views.CommentListView.as_view(), name="verse_comments"),
        path("<int:verse_id>/original-text/", views.OriginalTextView.as_view(), name="verse_original_text"),
        path("<int:verse_id>/morphology/", views.VerseMorphologyView.as_view(), name="verse_morphology"),
        path("<int:verse_id>/references/", views.VerseCrossReferenceView.as_view(), name="verse_references"),
        path("<int:verse_id>/references/save/", views.SaveCrossReferencesView.as_view(), name="verse_references_save"),
        path("word-analysis/<str:word>/", views.WordAnalysisView.as_view(), name="word_analysis"),
        path("word-frequency/<str:book_name>/", views.WordFrequencyView.as_view(), name="word_frequency"),
    ])),

    # 🔗 CROSS-REFERENCES
    path("cross-references/", include([
        path("verse/<int:verse_id>/", views.VerseCrossReferenceView.as_view(), name="crossrefs_by_verse"),
        path("by-theme/<int:theme_id>/", views.CrossReferencesByThemeView.as_view(), name="crossrefs_by_theme"),
        path("by-keyword/<str:keyword>/", views.CrossReferencesByKeywordView.as_view(), name="crossrefs_by_keyword"),
        path("chain/<int:verse_id>/", views.ReferenceChainView.as_view(), name="crossrefs_chain"),
        path("parallels/ot-nt/", views.OTNTParallelsView.as_view(), name="crossrefs_ot_nt"),
        path("save/<int:verse_id>/", views.SaveCrossReferencesView.as_view(), name="crossrefs_save"),
    ])),

    # 📖 VERSIONS
    path("versions/", include([
        path("", views.VersionListView.as_view(), name="versions_list"),
        path("<str:abbreviation>/", views.VersionDetailView.as_view(), name="version_detail"),
        path("by-language/<str:language_code>/", views.VersionsByLanguageView.as_view(), name="versions_by_language"),
        path("comparison/<str:reference>/", views.VersionComparisonView.as_view(), name="version_comparison"),
        path("language-comparison/<str:reference>/", views.LanguageComparisonView.as_view(), name="language_comparison"),
    ])),

    # 🔍 SEARCH
    path("search/", include([
        path("", views.AdvancedSearchView.as_view(), name="search_advanced"),
        path("global/", views.GlobalSearchView.as_view(), name="search_global"),
        path("reference/<str:reference>/", views.ReferenceSearchView.as_view(), name="search_reference"),
    ])),

    # 🗺️ CONTEXT
    path("context/", include([
        path("chapter/<str:book_name>/<int:chapter>/", views.ChapterContextView.as_view(), name="chapter_context"),
        path("verse/<int:verse_id>/", views.VerseContextView.as_view(), name="verse_context_detail"),
    ])),

    # 📍 GEOGRAPHY
    path("geography/", include([
        path("", views.PlaceListView.as_view(), name="places_list"),
        path("place/<str:place_name>/", views.PlaceDetailView.as_view(), name="place_detail"),
        path("maps/", views.BiblicalMapsView.as_view(), name="biblical_maps"),
        path("timeline/", views.BiblicalTimelineView.as_view(), name="biblical_timeline"),
    ])),

    # 👥 PEOPLE
    path("people/", include([
        path("", views.BiblicalPeopleListView.as_view(), name="people_list"),
        path("<str:person_name>/", views.PersonDetailView.as_view(), name="person_detail"),
        path("by-book/<str:book_name>/", views.PeopleByBookView.as_view(), name="people_by_book"),
    ])),

    # 📅 EVENTS
    path("events/", include([
        path("", views.BiblicalEventsListView.as_view(), name="events_list"),
        path("<str:event_name>/", views.EventDetailView.as_view(), name="event_detail"),
        path("chronology/", views.ChronologyView.as_view(), name="events_chronology"),
    ])),

    # 📖 DICTIONARY
    path("dictionary/", include([
        path("", views.DictionaryListView.as_view(), name="dictionary_list"),
        path("term/<str:term>/", views.DictionaryTermView.as_view(), name="dictionary_term"),
        path("search/", views.DictionarySearchView.as_view(), name="dictionary_search"),
    ])),

    # 🔤 CONCORDANCE
    path("concordance/", include([
        path("word/<str:word>/", views.ConcordanceView.as_view(), name="concordance_word"),
        path("strong/<str:strong_number>/", views.StrongsConcordanceView.as_view(), name="concordance_strong"),
    ])),

    # 🧭 NAVIGATION
    path("navigation/", include([
        path("next/<int:verse_id>/", views.NextVerseView.as_view(), name="navigation_next"),
        path("previous/<int:verse_id>/", views.PreviousVerseView.as_view(), name="navigation_previous"),
        path("context/<int:verse_id>/", views.VerseNavigationContextView.as_view(), name="navigation_context"),
    ])),

    # ⭐ RECOMMENDED
    path("recommended/", include([
        path("verses/", views.RecommendedVersesView.as_view(), name="recommended_verses"),
        path("daily/", views.DailyVerseView.as_view(), name="recommended_daily"),
        path("daily/<str:date>/", views.DailyVerseByDateView.as_view(), name="recommended_daily_by_date"),
        path("popular/", views.PopularVersesView.as_view(), name="recommended_popular"),
        path("seasonal/", views.SeasonalVersesView.as_view(), name="recommended_seasonal"),
    ])),

    # 📊 STATISTICS
    path("statistics/", include([
        path("overview/", views.BibleStatisticsView.as_view(), name="statistics_overview"),
        path("words/", views.WordStatisticsView.as_view(), name="statistics_words"),
        path("themes/", views.ThemeStatisticsView.as_view(), name="statistics_themes"),
        path("usage/", views.UsageStatisticsView.as_view(), name="statistics_usage"),
    ])),

    # 🎯 TOOLS  ⟵ (voltou)
    path("tools/", include([
        path("parallel-passages/", views.ParallelPassagesView.as_view(), name="tools_parallel_passages"),
        path("text-comparison/", views.TextComparisonToolView.as_view(), name="tools_text_comparison"),
        path("verse-networks/", views.VerseNetworksView.as_view(), name="tools_verse_networks"),
    ])),

    # 🔑 Auth & API Keys  ⟵ (novo include)
    path("auth/", include(("bible.apps.auth.urls", "bible_auth"), namespace="bible_auth")),

    # 🩺 Health & 📈 Metrics  ⟵ (mantidos aqui)
    path("health/", views.HealthCheckView.as_view(), name="health"),
    path("metrics/", views.MetricsView.as_view(), name="metrics"),
]


# bible/ai/urls.py
from django.urls import path
from . import views

app_name = "ai"

urlpatterns = [
    path("agents/", views.AgentListView.as_view(), name="ai_agents_list"),
    path("tools/", views.ToolListView.as_view(), name="ai_tools_list"),
    path("tools/<str:tool>/test/", views.ToolTestView.as_view(), name="ai_tool_test"),  # << NOVO
    path("agents/<str:name>/runs/", views.AgentRunCreateView.as_view(), name="ai_agent_run_create"),
    path("runs/<int:run_id>/", views.AgentRunDetailView.as_view(), name="ai_run_detail"),
    path("runs/<int:run_id>/approve/", views.AgentRunApproveView.as_view(), name="ai_run_approve"),
    path("runs/<int:run_id>/cancel/", views.AgentRunCancelView.as_view(), name="ai_run_cancel"),
]

# bible/apps/auth/urls.py
from django.urls import path
from . import views

app_name = "bible_auth"

urlpatterns = [
    path("api-keys/", views.APIKeyListCreateView.as_view(), name="api_keys_list_create"),
    path("api-keys/<int:pk>/", views.APIKeyRevokeView.as_view(), name="api_keys_revoke"),
    path("usage/", views.APIKeyUsageView.as_view(), name="api_keys_usage"),
    path("admin/usage/", views.AdminUsageView.as_view(), name="api_keys_admin_usage"),
]

# bible/apps/audio/urls.py
from django.urls import path
from . import views

app_name = "audio"

urlpatterns = [
    # Cache-first: se existir, 302 -> CDN; se em progresso 202; se não existir, cria job (se habilitado)
    path("verses/", views.VerseAudioView.as_view(), name="verses_audio"),

    # Status de job (polling)
    path("jobs/<uuid:job_id>/", views.AudioJobStatusView.as_view(), name="audio_job_status"),
]


# bible/apps/resources/urls.py
from django.urls import path
from . import views

app_name = "resources"

urlpatterns = [
    path("", views.ResourceListView.as_view(), name="resources_list"),
]



project_root/
├─ manage.py
├─ pyproject.toml / requirements.txt
│
├─ config/
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ urls.py                  # inclui bible.urls e bible.ai.urls + schema agregado
│  ├─ asgi.py / wsgi.py
│  └─ schema.py                # (se usar customizations do spectacular)
│
├─ bible/
│  ├─ __init__.py
│  ├─ urls.py                # (arquivo único que você montou)
│  ├─ views.py               # (se quiser centralizar simples)
│  ├─ ai/
│  │  ├─ __init__.py
│  │  ├─ registry.py         # Esqueleto de registry + tool adapter
│  │  ├─ services.py
│  │  ├─ urls.py
│  │  ├─ views.py
│  │  ├─ tools/
│  │  │  ├─ __init__.py
│  │  │  ├─ bible_tools.py       # adapters p/ Verses, CrossRefs, Search
│  │  │  └─ maintenance.py       # reindex embeddings, etc.
│  │  ├─ tasks.py                # Celery/RQ (opcional p/ jobs longos)
│  │  ├─ approvals.py            # fluxo de aprovação humana (opcional)
│  │  └─ permissions.py          # scopes ex.: ai:run, ai:tools:execute
│  ├─ apps/
│  │  ├─ auth/
│  │  │  ├─ __init__.py
│  │  │  ├─ urls.py              # /bible/auth/...
│  │  │  ├─ views.py             # endpoints de API Key, usage, etc.
│  │  │  ├─ serializers.py       # serializers dos endpoints de auth
│  │  │  ├─ authentication.py    # APIKeyAuthentication
│  │  │  ├─ permissions.py       # HasAPIScopes, etc.
│  │  │  ├─ throttling.py        # escopos/nomes de throttle por view
│  │  │  ├─ exceptions.py        # api_exception_handler (referenciado no REST_FRAMEWORK)
│  │  │  └─ tests/               # testes de auth
│  │  │     ├─ __init__.py
│  │  │     ├─ test_authentication.py
│  │  │     ├─ test_permissions.py
│  │  │     └─ test_api_keys_endpoints.py
│  │  ├─ audio/
│  │  │  ├─ __init__.py
│  │  │  ├─ urls.py            # /api/v1/bible/audio/...
│  │  │  ├─ views.py           # endpoints REST (cache-first)
│  │  │  ├─ serializers.py     # validação (versão, ref, voz, fmt)
│  │  │  ├─ services.py        # orquestra cache + job + provider
│  │  │  ├─ selectors.py       # consultas AudioClip/Job (read-only)
│  │  │  ├─ storage.py         # abstração S3/GCS/local
│  │  │  ├─ providers/
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ base.py         # synthesize(text, voice, rate, fmt) -> bytes
│  │  │  │  ├─ polly.py        # exemplo AWS Polly
│  │  │  │  └─ gcloud.py       # exemplo Google TTS
│  │  │  └─ tests/
│  │  └─ tests/
│  │  ├─ resources/
│  │  │  ├─ __init__.py
│  │  │  ├─ urls.py            # /api/v1/bible/resources/...
│  │  │  ├─ views.py           # listagem + filtros
│  │  │  ├─ serializers.py
│  │  │  ├─ client.py          # HTTP p/ blog (API externa)
│  │  │  ├─ selectors.py       # leitura + cache + join com client
│  │  │  └─ tests/
│  │  │
│  │  ├─ books/
│  │  │  ├─ __init__.py
│  │  │  ├─ views.py         # DRF views/viewsets
│  │  │  ├─ serializers.py   # DRF
│  │  │  ├─ schema.py        # tipos OpenAPI/parsers (opcional)
│  │  │  └─ tests/
│  │  ├─ verses/
│  │  │  ├─ __init__.py
│  │  │  ├─ views.py
│  │  │  ├─ serializers.py
│  │  │  ├─ schema.py
│  │  │  └─ tests/
│  │  ├─ themes/
│  │  ├─ crossrefs/
│  │  ├─ versions/
│  │  ├─ search/
│  │  ├─ context/
│  │  ├─ geography/
│  │  ├─ people/
│  │  ├─ events/
│  │  ├─ dictionary/
│  │  ├─ concordance/
│  │  ├─ navigation/
│  │  ├─ recommended/
│  │  ├─ statistics/
│  │  └─ tools/
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ books.py
│  │  ├─ verses.py
│  │  ├─ themes.py
│  │  ├─ people.py
│  │  ├─ places.py
│  │  ├─ events.py
│  │  ├─ dictionary.py
│  │  ├─ crossrefs.py        # CrossReference
│  │  ├─ comments.py         # Commentary*
│  │  ├─ rag.py              # TextChunk, RetrievalLog
│  │  └─ auth.py             # APIKey, RequestLog, APIQuota
│  ├─ admin.py
│  ├─ permissions.py         # regras DRF de acesso
│  ├─ pagination.py          # paginação padrão
│  ├─ filters.py             # filtros globais (django-filters)
│  └─ tests/
│
├─ common/
│  ├─ __init__.py
│  ├─ utils.py               # helpers (refs, parse "Jo 3:16", formatters)
│  ├─ cache.py               # cache helpers (Redis)
│  ├─ errors.py              # exceções customizadas
│  ├─ constants.py           # enums: versifications, scopes, canonical maps
│  ├─ monitoring.py          # métricas Prometheus, health checks
│  └─ logging.py             # logger customizado (opcional)
│
├─ scripts/
│  ├─ load_seed_data.py      # popular a base (books, verses, themes)
│  ├─ import_versions.py     # importar traduções (PT-BR, EN, etc.)
│  ├─ reindex_search.py      # rebuild de índices (es, pg_trgm)
│  └─ embeddings.py          # gerar embeddings p/ RAG
│
└─ docs/
   ├─ api.md                 # README da API (endpoints + exemplos)
   ├─ decisions.md           # ADRs de arquitetura
   ├─ BIBLE_API_STRUCTURE.md # estrutura técnica completa
   └─ BIBLE_API_README.md    # visão geral p/ devs


# bible/models/agents.py
from django.db import models
from django.conf import settings


class RunStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    NEEDS_APPROVAL = "needs_approval", "Needs approval"


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class AIAgent(models.Model):
    name = models.CharField(max_length=80, unique=True)  # ex: "themer", "xrefs-suggester"
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    scopes = models.JSONField(default=list)              # ["themes:write", "crossrefs:suggest"]
    temperature = models.FloatField(default=0.2)
    max_steps = models.PositiveIntegerField(default=8)

    class Meta:
        db_table = "ai_agents"
        constraints = [
            models.CheckConstraint(check=models.Q(temperature__gte=0.0) & models.Q(temperature__lte=2.0),
                                   name="aiagent_temperature_0_2"),
            models.CheckConstraint(check=models.Q(max_steps__gte=1), name="aiagent_max_steps_pos"),
        ]

    def __str__(self):
        return self.name


class AITool(models.Model):
    """
    Mapeia um nome de ferramenta chamável pelo agente a uma função backend (service/selector).
    """
    name = models.CharField(max_length=80, unique=True)  # ex: "apply_theme_tags"
    description = models.TextField()
    requires_approval = models.BooleanField(default=False)
    allowed_scopes = models.JSONField(default=list)      # ex: ["themes:write"]

    class Meta:
        db_table = "ai_tools"

    def __str__(self):
        return self.name


class AgentRun(models.Model):
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="runs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="ai_runs")
    input_payload = models.JSONField()                   # query, filtros, target range...
    plan = models.JSONField(null=True, blank=True)       # chain-of-thought resumido (sem PII)
    tools_called = models.JSONField(default=list)        # [{"tool":"...", "args":{...}, "result_id":123}, ...]
    status = models.CharField(max_length=20, choices=RunStatus.choices,
                              default=RunStatus.RUNNING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ai_agent_runs"
        indexes = [
            models.Index(fields=["agent", "created_at"], name="agent_runs_agent_created_idx"),
            models.Index(fields=["status", "created_at"], name="agent_runs_status_created_idx"),
        ]

    def __str__(self):
        return f"Run #{self.pk} - {self.agent.name} - {self.status}"


class PendingApproval(models.Model):
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="approvals")
    tool = models.ForeignKey(
        AITool,
        on_delete=models.PROTECT,
        related_name="approvals",
        null=True,
        blank=True,
    )
    tool_name = models.CharField(
        max_length=80,
        blank=True,
    )
    args = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ai_pending_approvals"
        indexes = [
            models.Index(fields=["status", "created_at"], name="approvals_status_created_idx"),
            models.Index(fields=["tool"], name="approvals_tool_idx"),  # <- novo índice
        ]

    def save(self, *args, **kwargs):
        # garante coerência do cache
        if self.tool and not self.tool_name:
            self.tool_name = self.tool.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Approval #{self.pk} - {self.tool_name or 'unknown'} - {self.status}"


# bible/models/auth.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys")
    key = models.CharField(max_length=40, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    scopes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_keys"
        indexes = [
            models.Index(fields=["user", "created_at"], name="apikey_user_created_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({'revoked' if self.revoked else 'active'})"

    @property
    def is_active(self) -> bool:
        return (not self.revoked) and (self.expires_at is None or self.expires_at > timezone.now())


class RequestLog(models.Model):
    class Method(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"
        HEAD = "HEAD", "HEAD"
        OPTIONS = "OPTIONS", "OPTIONS"

    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True, related_name="request_logs")
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=Method.choices)
    status_code = models.IntegerField()
    response_time_ms = models.FloatField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "request_logs"
        indexes = [
            models.Index(fields=["created_at"], name="request_logs_created_idx"),
            models.Index(fields=["status_code"], name="request_logs_status_idx"),
            models.Index(fields=["method"], name="request_logs_method_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(status_code__gte=100) & models.Q(status_code__lte=599),
                                   name="reqlog_status_http_range"),
            models.CheckConstraint(check=models.Q(response_time_ms__gte=0), name="reqlog_resp_time_nonneg"),
        ]

    def __str__(self):
        return f"{self.method} {self.path} [{self.status_code}]"


class APIQuota(models.Model):
    api_key = models.OneToOneField(APIKey, on_delete=models.CASCADE, related_name="quota")
    limit_per_day = models.IntegerField(default=1000)
    limit_per_minute = models.IntegerField(default=60)
    used_today = models.IntegerField(default=0)
    last_reset = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "api_quotas"
        constraints = [
            models.CheckConstraint(check=models.Q(limit_per_day__gte=0), name="quota_day_nonneg"),
            models.CheckConstraint(check=models.Q(limit_per_minute__gte=0), name="quota_min_nonneg"),
            models.CheckConstraint(check=models.Q(used_today__gte=0), name="quota_used_nonneg"),
        ]

    def __str__(self):
        return f"Quota for {self.api_key_id}: {self.used_today}/{self.limit_per_day}"




# bible/models/books.py

from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ex: 'pt-BR', 'en'

    class Meta:
        db_table = "languages"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class License(models.Model):
    code = models.CharField(max_length=50, unique=True)  # 'PD', 'CC-BY-SA-4.0'
    name = models.CharField(max_length=150)
    url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "licenses"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Version(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="versions", null=True)
    code = models.CharField(max_length=40, db_index=True)  # ex: 'PT-BR_ARA', 'EN_KJV'
    name = models.CharField(max_length=100)
    versification = models.CharField(max_length=40, default="KJV")  # 'KJV','Vulgate',...
    copyright = models.CharField(max_length=200, null=True, blank=True)
    permissions = models.TextField(null=True, blank=True)
    license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name="versions")
    source_url = models.URLField(null=True, blank=True)

    class Meta:
        db_table = "versions"
        ordering = ["language_id", "code"]
        constraints = [
            models.UniqueConstraint(fields=["language", "code"], name="uniq_version_language_code"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Testament(models.Model):
    name = models.CharField(max_length=45, blank=True, null=True)  # AT/NT
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "testaments"
        ordering = ["id"]

    def __str__(self):
        return self.name or "Testament"


class CanonicalBook(models.Model):
    """
    Um por livro do cânon, independente de idioma/versão.
    """
    osis_code = models.CharField(max_length=12, unique=True)  # 'Gen','Exod','Ps','Matt',...
    canonical_order = models.PositiveIntegerField()
    testament = models.ForeignKey(Testament, on_delete=models.CASCADE, related_name="canonical_books")
    is_deuterocanonical = models.BooleanField(default=False)

    class Meta:
        db_table = "canonical_books"
        ordering = ["canonical_order"]
        constraints = [
            models.CheckConstraint(check=models.Q(canonical_order__gte=1), name="book_canonical_order_pos"),
        ]

    def __str__(self):
        return self.osis_code


class BookName(models.Model):
    """
    Nomes/abreviações por idioma (e opcionalmente por versão).
    """
    canonical_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="names")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="book_names")
    name = models.CharField(max_length=60)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=True, blank=True, related_name="book_names")

    class Meta:
        db_table = "book_names"
        ordering = ["canonical_book_id", "language_id"]
        constraints = [
            # genérico por idioma (quando version é NULL)
            models.UniqueConstraint(
                fields=["canonical_book", "language"],
                condition=models.Q(version__isnull=True),
                name="uniq_bookname_lang_when_version_null",
            ),
            # específico por versão
            models.UniqueConstraint(
                fields=["canonical_book", "language", "version"],
                condition=models.Q(version__isnull=False),
                name="uniq_bookname_lang_version_when_version_not_null",
            ),
        ]
        indexes = [
            models.Index(fields=["canonical_book", "language"], name="bookname_book_lang_idx"),
        ]

    def __str__(self):
        suffix = f" ({self.version.code})" if self.version_id else ""
        return f"{self.name} [{self.language.code}]{suffix}"



# bible/models/verses.py
from django.db import models
from .books import Version, CanonicalBook


class Verse(models.Model):
    """
    Texto por versão.
    """
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="verses", db_index=True)
    canonical_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="verses", db_index=True)
    chapter = models.PositiveIntegerField(db_index=True)
    verse = models.PositiveIntegerField(db_index=True)
    text = models.TextField()

    class Meta:
        db_table = "verses"
        constraints = [
            models.UniqueConstraint(
                fields=["version", "canonical_book", "chapter", "verse"],
                name="uniq_verse_by_version_book_chap_verse",
            ),
            models.CheckConstraint(check=models.Q(chapter__gte=1), name="verse_chapter_pos"),
            models.CheckConstraint(check=models.Q(verse__gte=1), name="verse_number_pos"),
        ]
        indexes = [
            models.Index(fields=["version", "canonical_book", "chapter", "verse"], name="v_book_chap_verse_idx"),
        ]

    def __str__(self):
        return f"{self.version.code}:{self.canonical_book.osis_code} {self.chapter}:{self.verse}"


# bible/models/themes.py
from django.db import models
from .verses import Verse


class Theme(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        db_table = "themes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class VerseTheme(models.Model):
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="theme_links")
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="verse_links")

    class Meta:
        db_table = "verse_themes"
        constraints = [
            models.UniqueConstraint(fields=["verse", "theme"], name="uniq_verse_theme"),
        ]
        indexes = [
            models.Index(fields=["theme"], name="vt_theme_idx"),
        ]

    def __str__(self):
        return f"{self.verse_id} ↔ {self.theme.name}"


# bible/models/crossrefs.py
from django.db import models
from django.db.models import F, Q
from .books import CanonicalBook


class CrossReference(models.Model):
    """
    Relação entre um trecho bíblico e outro (agnóstico de versão).
    """
    from_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="x_from")
    from_chapter = models.PositiveIntegerField()
    from_verse = models.PositiveIntegerField()
    to_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="x_to")
    to_chapter = models.PositiveIntegerField()
    to_verse_start = models.PositiveIntegerField()
    to_verse_end = models.PositiveIntegerField()

    source = models.CharField(max_length=120, blank=True, null=True)  # ex: TSK, UBS
    source_ref = models.CharField(max_length=255, blank=True, null=True)
    confidence = models.FloatField(default=1.0)  # peso, de 0 a 1
    explanation = models.TextField(blank=True, null=True)  # nota explicativa
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cross_references"
        indexes = [
            models.Index(fields=["from_book", "from_chapter", "from_verse"], name="cr_from_idx"),
            models.Index(fields=["to_book", "to_chapter", "to_verse_start", "to_verse_end"], name="cr_to_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "from_book", "from_chapter", "from_verse",
                    "to_book", "to_chapter", "to_verse_start", "to_verse_end", "source"
                ],
                name="uniq_crossref_full",
            ),
            models.CheckConstraint(check=Q(to_verse_end__gte=F("to_verse_start")), name="cr_to_end_gte_start"),
            models.CheckConstraint(check=Q(confidence__gte=0.0) & Q(confidence__lte=1.0),
                                   name="cr_confidence_0_1"),
        ]

    def __str__(self):
        return f"{self.from_book.osis_code} {self.from_chapter}:{self.from_verse} → {self.to_book.osis_code} {self.to_chapter}:{self.to_verse_start}-{self.to_verse_end}"

# bible/models/comments.py
from django.db import models
from django.conf import settings
from .books import License, Language, CanonicalBook
from .verses import Verse


class CommentarySource(models.Model):
    """
    Metadados do acervo (ex.: 'Matthew Henry', 'TSK', 'Barnes', 'Bíblia de Genebra').
    """
    name = models.CharField(max_length=120)
    short_code = models.CharField(max_length=40, unique=True)  # 'MHCC','TSK','BARNES'
    license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name="commentary_sources")
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name="commentary_sources")
    url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "commentary_sources"
        ordering = ["short_code"]

    def __str__(self):
        return self.name


class CommentaryEntry(models.Model):
    """
    Comentário por referência canônica; pode cobrir um range (ex.: 3:14-16).
    """
    source = models.ForeignKey(CommentarySource, on_delete=models.CASCADE, related_name="entries")
    book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="commentary_entries")
    chapter = models.PositiveIntegerField()
    verse_start = models.PositiveIntegerField()
    verse_end = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True, null=True)
    body_md = models.TextField(blank=True, null=True)
    body_html = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "commentary_entries"
        indexes = [
            models.Index(fields=["source", "book", "chapter", "verse_start", "verse_end"],
                         name="commentary_entry_ref_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "book", "chapter", "verse_start", "verse_end"],
                name="uniq_commentary_source_ref",
            ),
            models.CheckConstraint(check=models.Q(verse_end__gte=models.F("verse_start")),
                                   name="commentary_end_gte_start"),
        ]

    def __str__(self):
        return f"{self.source.short_code}: {self.book.osis_code} {self.chapter}:{self.verse_start}-{self.verse_end}"


class VerseComment(models.Model):
    """
    Comentário do USUÁRIO.
    """
    verse = models.ForeignKey(Verse, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verse_comments")
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verse_comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="vcomment_user_created_idx"),
        ]

    def __str__(self):
        return f"Comment #{self.pk} on verse {self.verse_id}"


# bible/models/rag.py

from django.db import models
from .verses import Verse
from .comments import CommentaryEntry


class TextChunk(models.Model):
    """
    Trecho de texto (verso, comentário, dicionário) usado para embeddings.
    """
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, null=True, blank=True, related_name="chunks")
    commentary = models.ForeignKey(CommentaryEntry, on_delete=models.CASCADE, null=True, blank=True, related_name="chunks")
    content = models.TextField()
    chunk_index = models.PositiveIntegerField()  # ordem do pedaço
    # Dica: considere usar pgvector em produção.
    embedding = models.BinaryField(null=True, blank=True)

    class Meta:
        db_table = "text_chunks"
        indexes = [
            models.Index(fields=["verse", "commentary"], name="chunk_verse_commentary_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(chunk_index__gte=0), name="chunk_index_nonneg"),
        ]

    def __str__(self):
        target = f"verse:{self.verse_id}" if self.verse_id else f"commentary:{self.commentary_id}"
        return f"Chunk {self.chunk_index} -> {target}"


class RetrievalLog(models.Model):
    """
    Log de operações de recuperação (para auditoria/feedback de RAG).
    """
    query = models.TextField()
    retrieved_chunks = models.JSONField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retrieval_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retrieval_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="retrieval_created_idx"),
        ]

    def __str__(self):
        return f"Retrieval #{self.pk}"

# bible/models/audio.py
from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from .books import Version, CanonicalBook


class AudioStatus(models.TextChoices):
    READY = "ready", "Ready"
    STALE = "stale", "Stale"
    DELETED = "deleted", "Deleted"


class JobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class AudioFormat(models.TextChoices):
    MP3 = "mp3", "MP3"
    OGG = "ogg", "OGG"
    WAV = "wav", "WAV"


class AudioProvider(models.TextChoices):
    POLLY = "polly", "AWS Polly"
    GCLOUD = "gcloud", "Google TTS"
    AZURE = "azure", "Azure TTS"
    EDGE = "edge", "Edge TTS"
    CUSTOM = "custom", "Custom"


class AudioClip(models.Model):
    """
    Áudio sintetizado e armazenado (cache-first).
    Unicidade garantida por 'cache_key', que deve incorporar:
      version, book, chapter, start..end, voice, rate, format e hash do texto.
    """
    cache_key = models.CharField(max_length=80, unique=True, db_index=True)

    # referência bíblica
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="audio_clips")
    book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="audio_clips")
    chapter = models.PositiveIntegerField()
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()

    # parâmetros de síntese
    voice = models.CharField(max_length=64, blank=True, default="")
    rate = models.FloatField(default=1.0)  # fator de fala (0.5–1.5 recomendado)
    fmt = models.CharField(max_length=8, choices=AudioFormat.choices, default=AudioFormat.MP3)
    provider = models.CharField(max_length=16, choices=AudioProvider.choices, default=AudioProvider.POLLY)

    # armazenamento / entrega
    object_key = models.CharField(max_length=512, help_text="Chave/Path no storage (ex.: S3 object key).")
    cdn_url = models.URLField(max_length=1024, blank=True, default="", help_text="URL CDN (opcional; pode ser derivado).")
    etag = models.CharField(max_length=128, blank=True, default="")
    content_type = models.CharField(max_length=64, blank=True, default="audio/mpeg")

    # integridade e ciclo de vida
    text_hash = models.CharField(max_length=64, help_text="SHA-1/256 do texto fonte concatenado.")
    status = models.CharField(max_length=16, choices=AudioStatus.choices, default=AudioStatus.READY, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_access_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audio_clips"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["version", "book", "chapter"], name="audio_clip_ref_idx"),
            models.Index(fields=["status", "created_at"], name="audio_clip_status_created_idx"),
            models.Index(fields=["text_hash"], name="audio_clip_text_hash_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=Q(chapter__gte=1), name="audio_clip_chapter_pos"),
            models.CheckConstraint(check=Q(start__gte=1) & Q(end__gte=F("start")), name="audio_clip_range_valid"),
            models.CheckConstraint(check=Q(rate__gte=0.5) & Q(rate__lte=1.5), name="audio_clip_rate_0_1_5"),
        ]

    def __str__(self) -> str:
        return f"{self.cache_key} ({self.version.code} {self.book.osis_code} {self.chapter}:{self.start}-{self.end})"

    @property
    def url(self) -> str:
        """
        Preferir 'cdn_url' persistido; caso ausente, derivar de settings.AUDIO_CDN_BASE_URL + object_key.
        """
        if self.cdn_url:
            return self.cdn_url
        base = getattr(settings, "AUDIO_CDN_BASE_URL", "").rstrip("/")
        return f"{base}/{self.object_key.lstrip('/')}" if base and self.object_key else ""


class AudioJob(models.Model):
    """
    Job assíncrono de síntese.
    Regras:
      - No máximo 1 job 'in-flight' por cache_key (partial unique).
      - Ao concluir com sucesso, aponta para o AudioClip gerado.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cache_key = models.CharField(max_length=80, db_index=True)
    params = models.JSONField(help_text="Payload normalizado usado na síntese (inclui referência e opções).")
    status = models.CharField(max_length=16, choices=JobStatus.choices, default=JobStatus.QUEUED, db_index=True)
    clip = models.ForeignKey(AudioClip, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    error = models.TextField(blank=True, null=True)

    attempts = models.PositiveSmallIntegerField(default=0)
    priority = models.PositiveSmallIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "audio_jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cache_key", "status"], name="audio_job_key_status_idx"),
            models.Index(fields=["status", "created_at"], name="audio_job_status_created_idx"),
        ]
        constraints = [
            # Requer PostgreSQL para partial unique constraint:
            models.UniqueConstraint(
                fields=["cache_key"],
                condition=Q(status__in=[JobStatus.QUEUED, JobStatus.RUNNING]),
                name="uniq_audio_job_cache_key_inflight",
            ),
            models.CheckConstraint(check=Q(priority__gte=0), name="audio_job_priority_nonneg"),
            models.CheckConstraint(check=Q(attempts__gte=0), name="audio_job_attempts_nonneg"),
        ]

    def __str__(self) -> str:
        return f"{self.id} [{self.status}] {self.cache_key}"


# bible/models/resources.py
# bible/models/resources.py
from __future__ import annotations

from django.db import models
from .books import Language, CanonicalBook
from .themes import Theme


class ResourceType(models.TextChoices):
    ARTICLE = "article", "Article"
    VIDEO = "video", "Video"
    PODCAST = "podcast", "Podcast"
    OTHER = "other", "Other"


class ExternalProvider(models.Model):
    """Cadastro do provedor externo (seu blog, YouTube, etc.)."""
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    api_base_url = models.URLField(blank=True, default="")
    site_base_url = models.URLField(blank=True, default="")
    enabled = models.BooleanField(default=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "content_providers"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class StudyResourceLink(models.Model):
    """
    Ponte para um recurso externo (sem armazenar o corpo).
    Mantemos snapshots leves para listagem/SEO.
    """
    provider = models.ForeignKey(ExternalProvider, on_delete=models.PROTECT, related_name="resources")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name="resource_links")

    external_id = models.CharField(max_length=120)            # ID na API externa
    external_slug = models.SlugField(max_length=160, blank=True, default="")

    type = models.CharField(max_length=12, choices=ResourceType.choices, default=ResourceType.ARTICLE)

    # snapshots (opcionais; não guardamos body)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default="")
    cover_image_url = models.URLField(blank=True, default="")
    canonical_url = models.URLField(blank=True, default="")   # URL pública no site do blog
    api_url = models.URLField(blank=True, default="")         # endpoint do recurso na API externa

    status = models.CharField(max_length=12, default="published", db_index=True)  # espelho simples
    themes = models.ManyToManyField(Theme, blank=True, related_name="resource_links")

    extra = models.JSONField(default=dict, blank=True)        # metadados específicos do provedor

    # auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "study_resource_links"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["provider", "external_id"], name="reslink_provider_extid_idx"),
            models.Index(fields=["language", "published_at"], name="reslink_lang_pub_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_id"], name="uniq_reslink_provider_extid"),
        ]

    def __str__(self) -> str:
        return f"{self.title} [{self.provider.slug}]"


class StudyResourceRef(models.Model):
    """
    Mapeia o recurso externo a passagens bíblicas (por range canônico).
    """
    resource = models.ForeignKey(StudyResourceLink, on_delete=models.CASCADE, related_name="refs")
    book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="resource_refs")
    chapter = models.PositiveIntegerField()
    verse_start = models.PositiveIntegerField()
    verse_end = models.PositiveIntegerField()

    role = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Opcional: 'primary', 'secondary', etc.",
    )
    note = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        db_table = "study_resource_refs"
        ordering = ["resource_id", "book_id", "chapter", "verse_start"]
        indexes = [
            models.Index(fields=["book", "chapter", "verse_start", "verse_end"], name="srref_ref_idx"),
            models.Index(fields=["resource"], name="srref_resource_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "book", "chapter", "verse_start", "verse_end", "role"],
                name="uniq_srref_resource_ref_role",
            ),
            models.CheckConstraint(check=models.Q(chapter__gte=1), name="srref_chapter_pos"),
            models.CheckConstraint(
                check=models.Q(verse_start__gte=1) & models.Q(verse_end__gte=models.F("verse_start")),
                name="srref_range_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.resource_id} → {self.book.osis_code} {self.chapter}:{self.verse_start}-{self.verse_end}"


# bible/models/__init__.py
# Facilita imports planos: from bible.models import Verse, Theme, ...
from .agents import AIAgent, AITool, AgentRun, PendingApproval
from .auth import APIKey, RequestLog, APIQuota
from .books import Language, License, Version, Testament, CanonicalBook, BookName
from .verses import Verse
from .themes import Theme, VerseTheme
from .crossrefs import CrossReference
from .comments import CommentarySource, CommentaryEntry, VerseComment
from .rag import TextChunk, RetrievalLog
from .audio import AudioClip, AudioJob
from .resources import ExternalProvider, StudyResourceLink, StudyResourceRef




# bible/apps/auth/exceptions.py

import logging
import uuid
from typing import Optional, Any, Dict

from django.conf import settings
from django.http import Http404
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    Throttled,
    ValidationError,
    NotFound,
    MethodNotAllowed,
    ParseError,
    UnsupportedMediaType,
    NotAcceptable,
    PermissionDenied,
)

try:
    import sentry_sdk  # opcional
except Exception:  # pragma: no cover
    sentry_sdk = None

logger = logging.getLogger("api.errors")


class DomainError(APIException):
    """Exceção de domínio p/ usar nos services (ex.: regras de negócio)."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Domain error."
    default_code = "domain_error"

    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail=detail, code=code or self.default_code)


def _request_id(context) -> str:
    req = context.get("request")
    rid = None
    if req:
        rid = req.headers.get("X-Request-ID") or getattr(req, "request_id", None)
    return rid or uuid.uuid4().hex


def _log(exc, context, resp: Optional[Response], request_id: str) -> None:
    req = context.get("request")
    meta = {
        "request_id": request_id,
        "path": getattr(req, "path", None),
        "method": getattr(req, "method", None),
        "user_id": getattr(getattr(req, "user", None), "id", None),
        "status": getattr(resp, "status_code", 500),
        "code": getattr(exc, "default_code", None) or getattr(exc, "code", None),
        "view": context.get("view").__class__.__name__ if context.get("view") else None,
    }
    logger.warning("API error", extra={"props": meta}, exc_info=exc if settings.DEBUG else False)
    if sentry_sdk and getattr(settings, "SENTRY_DSN", None):
        sentry_sdk.set_context("api_error", meta)
        sentry_sdk.capture_exception(exc)


def _problem(
    detail: str,
    status_code: int,
    *,
    code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    errors: Optional[Any] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"detail": detail}
    if code:
        body["code"] = str(code)
    if errors is not None:
        body["errors"] = errors
    if extra:
        body["extra"] = extra
    if request_id:
        body["request_id"] = request_id
    return body


def _normalize_validation_errors(data) -> Any:
    # mantenha a estrutura original (DRF já traz um dict por campo);
    # se quiser, implemente um flatten aqui.
    return data


def api_exception_handler(exc, context) -> Optional[Response]:
    request_id = _request_id(context)
    resp = drf_exception_handler(exc, context)

    if resp is not None:
        # 422/400 – validação
        if isinstance(exc, (ValidationError, DjangoValidationError)):
            resp.data = _problem(
                "Invalid input.",
                resp.status_code,
                code="validation_error",
                errors=_normalize_validation_errors(resp.data),
                request_id=request_id,
            )
        # 401 – auth
        elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            resp.data = _problem(
                "Authentication credentials were not provided or are invalid.",
                resp.status_code,
                code="authentication_failed",
                request_id=request_id,
            )
            resp.headers["WWW-Authenticate"] = 'Api-Key realm="bible-api"'
        # 429 – throttle
        elif isinstance(exc, Throttled):
            wait = getattr(exc, "wait", None)
            resp.data = _problem(
                "Request was throttled. Try again later.",
                resp.status_code,
                code="throttled",
                request_id=request_id,
                extra={"retry_after": wait},
            )
            if wait is not None:
                resp.headers["Retry-After"] = str(int(wait))
        # 404
        elif isinstance(exc, (NotFound, Http404)):
            resp.data = _problem("Not found.", resp.status_code, code="not_found", request_id=request_id)
        # 403
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            resp.data = _problem(
                "You do not have permission to perform this action.",
                resp.status_code,
                code="permission_denied",
                request_id=request_id,
            )
        # 405/415/406/400 parse
        elif isinstance(exc, (MethodNotAllowed, ParseError, UnsupportedMediaType, NotAcceptable)):
            code = getattr(exc, "default_code", "error")
            resp.data = _problem(str(exc.detail), resp.status_code, code=code, request_id=request_id)
        # 4xx de domínio (services)
        elif isinstance(exc, DomainError):
            resp.data = _problem(
                str(exc.detail),
                resp.status_code,
                code=exc.get_codes(),
                request_id=request_id,
                extra=getattr(exc, "extra", None),
            )
        else:
            # mantém payload do DRF, mas injeta request_id
            if isinstance(resp.data, dict):
                resp.data.setdefault("request_id", request_id)

        _log(exc, context, resp, request_id)
        return resp

    # não tratado (500)
    data = _problem(
        "Internal server error.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        request_id=request_id,
    )
    resp = Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    _log(exc, context, resp, request_id)
    return resp



  📄 BIBLE_API_STRUCTURE.md

  - URLs organizadas com todos os endpoints expandidos
  - Estrutura de diretórios completa seguindo DDD
  - Notas de qualidade técnica com implementações práticas:
    - ✅ Versionamento da API (/api/v1/)
    - ✅ OpenAPI/Swagger automatizado
    - ✅ Cache Redis estratégico
    - ✅ Rate limiting por tipo de endpoint
    - ✅ Paginação e ordenação padrão
    - ✅ Convenções de nomenclatura
    - ✅ Permissions e authentication
    - ✅ Monitoring & observability
    - ✅ Testing strategy

  📚 BIBLE_API_README.md

  - Overview profissional da API
  - Quick start com exemplos práticos
  - Domínios detalhados de cada funcionalidade
  - Performance metrics e estratégias
  - Casos de uso reais com código
  - Roadmap e planejamento futuro
  - Documentação de suporte

  🔥 Principais Melhorias Propostas:

  1. Qualidade Técnica

  - Versionamento: /api/v1/bible/
  - Cache inteligente: Dados bíblicos permanentes, buscas 1h
  - Rate limiting: Proteção contra abuso
  - Swagger/OpenAPI: Documentação automática

  2. Organização

  - URLs RESTful: Padrões consistentes
  - Estrutura modular: Apps por domínio
  - Separação clara: Services, selectors, repositories
  - Testing: Estratégia de testes abrangente

  3. Performance

  - Cache Redis: Para endpoints pesados
  - Paginação: 10-20 itens conforme contexto
  - Throttling: Diferentes limites por tipo de uso
  - Indexação: Otimizada para buscas

  4. Developer Experience

  - Swagger UI: Interface de testes
  - Exemplos práticos: Casos de uso reais
  - Documentação clara: Múltiplos níveis de detalhamento
  - Convenções: Nomenclatura consistente


View (API Layer)
   │
   ├──> Serializer (validações de dados)
   │
   ├──> Service (regras de negócio compostas, escrita)
   │        │
   │        └──> Manager/QuerySet (selectors/repos natural do Django)
   │
   └──> Manager/QuerySet direto (quando é só leitura)



#settings.py

# --- AUDIO / TTS -------------------------------------------------------------
AUDIO_ON_DEMAND_ENABLED = True           # liga/desliga geração sob demanda
AUDIO_PROVIDER = "polly"                 # "polly" | "gcloud" | "edge" | ...
AUDIO_DEFAULT_VOICE = {                  # defaults por idioma
    "pt-BR": "Maria",
    "en": "Joanna",
}
AUDIO_ALLOWED_FORMATS = ["mp3", "ogg", "wav"]
AUDIO_DEFAULT_FORMAT = "mp3"
AUDIO_RATE_MIN = 0.5
AUDIO_RATE_MAX = 1.5

# armazenamento/CDN
AUDIO_STORAGE = "s3"                     # "s3" | "gcs" | "local"
AUDIO_BUCKET = "bible-audio"
AUDIO_CDN_BASE_URL = "https://cdn.example.com/audio/"
AUDIO_OBJECT_TTL = 365 * 24 * 3600       # 1 ano (cache CDN)

# licenças e versões
AUDIO_REQUIRE_VERSION_TTS_ALLOWED = True # valida se a versão permite TTS (campo futuro)

# --- APPS CORE ---------------------------------------------------------------
INSTALLED_APPS = [
    # 3rd
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    # habilite só se for usar agora:
    # "corsheaders",
    # "django_prometheus",  # se expor /metrics
    # project
    "bible",
]

# --- MIDDLEWARE --------------------------------------------------------------
MIDDLEWARE = [
    # "django_prometheus.middleware.PrometheusBeforeMiddleware",  # se usar prometheus
    # "corsheaders.middleware.CorsMiddleware",                    # se usar CORS já
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "django_prometheus.middleware.PrometheusAfterMiddleware",   # se usar prometheus
]

# --- DRF --------------------------------------------------------------------
# settings.py
REST_FRAMEWORK = {
    # 1) Paginação padrão (use sua classe para page_size_query_param e max_page_size)
    "DEFAULT_PAGINATION_CLASS": "bible.pagination.DefaultPagination",
    "PAGE_SIZE": 20,

    # 2) Filtros e ordenação (SearchFilter pode ser pesado; habilite por view)
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        # "rest_framework.filters.SearchFilter",  # habilite por view onde fizer sentido
    ],
    "ORDERING_PARAM": "ordering",   # ex: ?ordering=-created_at
    # "SEARCH_PARAM": "q",          # descomente se quiser padronizar ?q= ao invés de ?search=

    # 3) Schema OpenAPI (drf-spectacular)
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    # 4) Autenticação: Api-Key + Session (útil para Swagger/Browsable no DEV)
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "bible.apps.auth.authentication.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],

    # 5) Permissões: seguro por padrão; abra explicitamente o que for público
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
        # Dica: aplique bible.apps.auth.permissions.HasAPIScopes nas views que exigem escopo.
    ],

    # 6) Throttling (global + por escopo). Ajuste as taxas por ambiente.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",      # visitantes sem key
        "user": "600/minute",     # autenticados
        # escopos por endpoint (use view.throttle_scope = "search" por ex.)
        "search": "120/minute",
        "write": "30/minute",
        "ai-run": "30/minute",
        "ai-tools": "60/minute",
        "audio": "120/minute",          # download/listen endpoints
        "audio-synthesize": "20/minute" # criação de jobs (custo$)
    },

    # 7) Parsers/Renderers: em PROD foque JSON; no DEV mantenha Browsable API
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        # "rest_framework.parsers.FormParser",     # habilite se tiver forms
        # "rest_framework.parsers.MultiPartParser",# habilite se tiver upload
    ],
    # Em produção, considere deixar só JSONRenderer (torna respostas menores e previsíveis).
    # No DEV, comente esta seção para manter o BrowsableAPI.
    # "DEFAULT_RENDERER_CLASSES": [
    #     "rest_framework.renderers.JSONRenderer",
    # ],

    # 8) Handler de exceções padronizado (estrutura consistente de erro)
    "EXCEPTION_HANDLER": "bible.apps.auth.exceptions.api_exception_handler",

    # 9) Metadata mais enxuta (menor custo em listas grandes)
    "DEFAULT_METADATA_CLASS": "rest_framework.metadata.SimpleMetadata",

    # 10) Formatos e coerção numérica
    "COERCE_DECIMAL_TO_STRING": False,  # mantém decimais como número (não string)
    "DATETIME_FORMAT": None,            # ISO-8601 (padrão)
    "DATE_FORMAT": None,                # ISO-8601 (padrão)
    "TIME_FORMAT": None,                # ISO-8601 (padrão)

    # 11) Test client do DRF envia JSON por padrão
    "TEST_REQUEST_DEFAULT_FORMAT": "json",

    # 12) Versionamento (opcional). Como você usa /api/v1/ estático, deixe comentado.
    # Para header versioning: aceite "Accept: application/json; version=1.0"
    # "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    # "DEFAULT_VERSION": "1.0",
}

# --- drf-spectacular ---------------------------------------------------------
SPECTACULAR_SETTINGS = {
    # prefixa rotas documentadas (evita “vazar” endpoints fora de /api/v1)
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
    "TITLE": "Bible API",
    "DESCRIPTION": "API bíblica com domínios (books, verses, themes, crossrefs, etc.) e camada de IA.",
    "VERSION": "1.0.0",
    "SERVERS": [{"url": "/"}],  # se estiver por trás de proxy, ajuste aqui
    "COMPONENT_SPLIT_REQUEST": True,
    "ENABLE_EXAMPLES": True,
    # opcional: limpa tags/ordenação no Swagger
    # "TAGS": [{"name": "bible"}, {"name": "ai"}, {"name": "auth"}],
}

# --- CORS (opcional; mantenha fechado até precisar) -------------------------
# from os import getenv
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = [
#     "https://app.seudominio.com",
#     "https://studio.seudominio.com",
# ]
# CORS_URLS_REGEX = r"^/api/.*$"
# CORS_ALLOW_CREDENTIALS = False

# --- CACHE (Redis recomendado; use quando começar a cachear selectors/views) -
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
#         },
#         "TIMEOUT": 60 * 60,  # default 1h (ajuste por view/selectors)
#     }
# }

# --- LOGGING (console; enxuto e útil) ---------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "WARNING"},
        "bible": {"handlers": ["console"], "level": "INFO"},
    },
}

# --- PROMETHEUS (se for expor /metrics) -------------------------------------
# DATABASES["default"]["ENGINE"] = "django_prometheus.db.backends.postgresql"
