from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.apps.auth"
    label = "bible_auth"
    verbose_name = "Bible Authentication"
