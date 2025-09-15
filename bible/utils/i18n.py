"""
Internationalization utilities for Bible API.
Implements language negotiation and resolution as per API_STANDARDS.md §6.
"""
import logging

from django.conf import settings
from django.http import HttpRequest

from bible.models import Language

logger = logging.getLogger(__name__)


def resolve_language(request: HttpRequest) -> str:
    """
    Resolve language from request with priority order:
    1. ?lang= query parameter
    2. Accept-Language header
    3. Default to 'en'

    Returns language code validated against Language model.
    Falls back through pt-BR → pt → en for Portuguese variants.

    Args:
        request: Django HttpRequest object

    Returns:
        str: Valid language code (e.g., 'en', 'pt', 'es')

    Examples:
        >>> request.GET = {'lang': 'pt'}
        >>> resolve_language(request)
        'pt'

        >>> request.META = {'HTTP_ACCEPT_LANGUAGE': 'pt-BR,pt;q=0.9,en;q=0.8'}
        >>> resolve_language(request)
        'pt'
    """
    # 1. Check ?lang= query parameter (highest priority)
    lang_param = request.GET.get("lang")
    if lang_param:
        validated_lang = _validate_language_code(lang_param)
        if validated_lang:
            logger.debug(f"Language resolved from ?lang= parameter: {validated_lang}")
            return validated_lang
        logger.warning(f"Invalid lang parameter '{lang_param}', falling back to Accept-Language")

    # 2. Parse Accept-Language header
    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    if accept_language:
        parsed_langs = _parse_accept_language(accept_language)
        for lang_code, _ in parsed_langs:
            validated_lang = _validate_language_code(lang_code)
            if validated_lang:
                logger.debug(f"Language resolved from Accept-Language: {validated_lang}")
                return validated_lang

    # 3. Default fallback
    default_lang = getattr(settings, "DEFAULT_LANGUAGE_CODE", "en")
    logger.debug(f"Language resolved to default: {default_lang}")
    return default_lang


def _validate_language_code(lang_code: str) -> str | None:
    """
    Validate language code against Language model with fallback logic.

    Implements fallback: pt-BR → pt → en

    Args:
        lang_code: Language code to validate

    Returns:
        Valid language code or None if not found
    """
    if not lang_code:
        return None

    # Normalize to lowercase
    lang_code = lang_code.strip().lower()

    # Try exact match first
    if Language.objects.filter(code=lang_code).exists():
        return lang_code

    # Handle Portuguese variants (pt-BR → pt)
    if lang_code.startswith("pt"):
        if Language.objects.filter(code="pt").exists():
            logger.debug(f"Fallback: {lang_code} → pt")
            return "pt"

    # Handle Spanish variants (es-ES → es)
    if lang_code.startswith("es"):
        if Language.objects.filter(code="es").exists():
            logger.debug(f"Fallback: {lang_code} → es")
            return "es"

    # Handle English variants (en-US → en)
    if lang_code.startswith("en"):
        if Language.objects.filter(code="en").exists():
            logger.debug(f"Fallback: {lang_code} → en")
            return "en"

    # No fallback for completely invalid codes in validation
    # The resolve_language function handles final 'en' fallback
    return None


def _parse_accept_language(accept_language: str) -> list:
    """
    Parse Accept-Language header into list of (language, quality) tuples.
    Sorted by quality score (highest first).

    Args:
        accept_language: Accept-Language header value

    Returns:
        List of (language_code, quality_score) tuples sorted by quality

    Examples:
        >>> _parse_accept_language('pt-BR,pt;q=0.9,en;q=0.8')
        [('pt-br', 1.0), ('pt', 0.9), ('en', 0.8)]
    """
    languages = []

    for lang_part in accept_language.split(","):
        lang_part = lang_part.strip()
        if not lang_part:
            continue

        # Handle quality parameter with flexible whitespace
        if ";" in lang_part:
            parts = lang_part.split(";")
            lang = parts[0].strip()
            quality = 1.0

            # Look for q= parameter
            for part in parts[1:]:
                part = part.strip()
                if part.startswith("q=") or part.startswith("q ="):
                    quality_str = part.split("=", 1)[1].strip()
                    try:
                        quality = float(quality_str)
                    except (ValueError, TypeError):
                        quality = 1.0
                    break
        else:
            lang = lang_part
            quality = 1.0

        lang = lang.strip().lower()
        languages.append((lang, quality))

    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)
    return languages


class LanguageMiddleware:
    """
    Middleware to resolve and attach language code to request object.
    Adds request.lang_code attribute for use in views/serializers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Resolve language and attach to request
        request.lang_code = resolve_language(request)

        response = self.get_response(request)

        # Add Vary header for language-sensitive responses
        # Only add if not already present to avoid duplicates
        if hasattr(request, "_language_sensitive") and request._language_sensitive:
            vary_header = response.get("Vary", "")
            if "Accept-Language" not in vary_header:
                if vary_header:
                    response["Vary"] = f"{vary_header}, Accept-Language"
                else:
                    response["Vary"] = "Accept-Language"

        return response


def mark_response_language_sensitive(request: HttpRequest):
    """
    Mark request as language-sensitive to automatically add Vary: Accept-Language header.

    Call this in views that return language-dependent content.

    Args:
        request: Django HttpRequest object
    """
    request._language_sensitive = True


def get_language_from_context(context) -> str:
    """
    Get language code from serializer context.

    Args:
        context: Serializer context dictionary

    Returns:
        str: Language code ('en', 'pt', etc.)
    """
    if not context:
        return "en"

    request = context.get("request")
    if request and hasattr(request, "lang_code"):
        return request.lang_code

    return "en"
