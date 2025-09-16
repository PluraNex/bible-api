# bible/apps.py
from django.apps import AppConfig


class BibleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bible"
    verbose_name = "Bible"


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.auth"
    label = "bible_auth"
    verbose_name = "Bible Authentication"

    def ready(self):
        # Registro manual da extensão OpenAPI após Django estar carregado
        from django.conf import settings

        if hasattr(settings, "SPECTACULAR_SETTINGS"):
            try:
                # Força o registro da extensão
                from bible.auth.openapi import ApiKeyAuthenticationExtension

                # Verifica se pode ser importada
                if hasattr(ApiKeyAuthenticationExtension, "target_class"):
                    print(f"🔐 ApiKeyAuthenticationExtension loaded: {ApiKeyAuthenticationExtension.name}")
            except Exception as e:
                print(f"⚠️ Failed to load OpenAPI extension: {e}")
