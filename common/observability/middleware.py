import time

from django.utils.deprecation import MiddlewareMixin

from .metrics import BUILD_INFO, LATENCY, REQUESTS


class ObservabilityMiddleware(MiddlewareMixin):
    """Capture per-request custom metrics with business labels (lang, version, view)."""

    _inited = False

    def __init__(self, get_response=None):
        super().__init__(get_response)
        if not ObservabilityMiddleware._inited:
            try:
                from django.conf import settings

                version = (
                    settings.SPECTACULAR_SETTINGS.get("VERSION", "v1")
                    if hasattr(settings, "SPECTACULAR_SETTINGS")
                    else "v1"
                )
            except Exception:
                version = "v1"
            BUILD_INFO.info({"service": "bible-api", "version": version})
            ObservabilityMiddleware._inited = True

    def __call__(self, request):
        start = time.perf_counter()

        # Resolve business labels
        lang = getattr(request, "lang_code", None) or request.GET.get("lang") or "unknown"
        version = request.GET.get("version") or "default"
        try:
            view_name = getattr(request.resolver_match, "view_name", None) or "unknown"
        except Exception:
            view_name = "unknown"

        response = self.get_response(request)

        # Observe latency and increment counters
        elapsed = time.perf_counter() - start
        try:
            LATENCY.labels(view=view_name, lang=lang, version=version).observe(elapsed)
            REQUESTS.labels(
                method=request.method,
                status=str(getattr(response, "status_code", 0)),
                view=view_name,
                lang=lang,
                version=version,
            ).inc()
        except Exception:
            # Metrics should never break requests
            pass

        return response
