"""
Django settings for Bible API project.
"""

from pathlib import Path

import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: [s.strip() for s in v.split(",")])
# Dev convenience: allow Docker service names for metrics scraping when DEBUG
if DEBUG:
    for host in ["web", "bible-api-web-1", "host.docker.internal"]:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "django_prometheus",
    "pgvector.django",
]

LOCAL_APPS = [
    "bible.apps.BibleConfig",  # label = bible
    "bible.auth.apps.BibleAuthConfig",  # Authentication app
    "bible.comments",  # Commentary app (legacy)
    "bible.commentaries",  # Commentaries domain (enriched)
    "bible.ai",  # pode deixar assim se não tiver AppConfig própria
    "bible.entities",  # Canonical entities domain
    "bible.symbols",  # Biblical symbols domain
    "bible.theology",  # Systematic theology domain
    "bible.themes",  # Biblical themes domain
    "bible.people",  # Unified person identity hub
    "bible.images",  # Biblical art images domain
    "bible.integration",  # Cross-domain integration (image↔entity matching)
    "bible.studies",  # User-authored biblical studies
    "common",
    "data",  # Data management commands
]


INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "common.middleware.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "bible.utils.i18n.LanguageMiddleware",  # Language resolution for i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.observability.middleware.ObservabilityMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL",
            default=f"postgresql://{config('DB_USER', default='bible_user')}:{config('DB_PASSWORD', default='bible_pass')}@{config('DB_HOST', default='localhost')}:{config('DB_PORT', default='5432')}/{config('DB_NAME', default='bible_api')}",
        )
    )
}

# Instrument Postgres engine for django-prometheus if applicable
try:
    engine = DATABASES["default"].get("ENGINE", "")
    if engine.endswith("postgresql") or engine.endswith("postgresql_psycopg2"):
        DATABASES["default"]["ENGINE"] = "django_prometheus.db.backends.postgresql"
except (KeyError, AttributeError, ValueError):
    pass

# pgvector tuning via env (session options) - HNSW + IVFFlat support
try:
    # Legacy IVFFlat support (mantido para compatibilidade)
    probes = config("PG_IVFFLAT_PROBES", default=10, cast=int)

    # HNSW parameters - CRÍTICOS para performance do RAG (T-RAG08)
    hnsw_ef_search = config("PG_HNSW_EF_SEARCH", default=40, cast=int)  # Balance speed/accuracy

    DATABASES["default"].setdefault("OPTIONS", {})
    opts = DATABASES["default"]["OPTIONS"]

    # Build optimized connection options
    connection_params = []

    # IVFFlat (legacy)
    if probes:
        connection_params.append(f"ivfflat.probes={probes}")

    # HNSW (novo - performance crítica)
    if hnsw_ef_search:
        connection_params.append(f"hnsw.ef_search={hnsw_ef_search}")

    # Apply parameters to connection string
    if connection_params:
        param_string = " -c ".join(connection_params)
        extra = f"-c {param_string}"

        if "options" in opts and opts["options"]:
            # Merge with existing options, avoiding duplicates
            existing = str(opts["options"])
            for param in connection_params:
                if f"-c {param}" not in existing:
                    existing = f"{existing} -c {param}".strip()
            opts["options"] = existing
        else:
            opts["options"] = extra

except (KeyError, AttributeError, ValueError):
    # Fail silently to avoid breaking other configurations
    pass

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# I18N Configuration
DEFAULT_LANGUAGE_CODE = "en"

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "bible.auth.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        # "rest_framework.throttling.AnonRateThrottle",
        # "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/hour",  # Aumentado para desenvolvimento
        "user": "10000/hour",  # Aumentado para desenvolvimento
    },
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

# Spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Bible API",
    "DESCRIPTION": "A comprehensive RESTful Bible API with AI integration",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    # OpenAPI 3.0 security schemes - CONFIGURAÇÃO CORRETA
    "SECURITY": [{"ApiKeyAuth": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "API Key authentication. Format: Api-Key your_api_key_here",
            }
        }
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080",
    cast=lambda v: [s.strip() for s in v.split(",")] if v else [],
)

# CORS additional settings
CORS_ALLOW_CREDENTIALS = True
# ⚠️ SEGURANÇA: Em produção, sempre defina CORS_ALLOW_ALL_ORIGINS=False
# e configure CORS_ALLOWED_ORIGINS com os domínios específicos permitidos
# Para desenvolvimento, permitir todas as origens quando DEBUG=True
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=DEBUG, cast=bool)

# CORS allowed headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "accept-language",
]

# CORS allowed methods
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "common.logging.ContextFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} [rid:{request_id}] {process:d} {thread:d} {message}",
            "style": "{",
            "defaults": {"request_id": "-"},
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_context"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
