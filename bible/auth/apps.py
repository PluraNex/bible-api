from django.apps import AppConfig


class BibleAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.auth"
    label = "bible_auth"  # Avoid conflict with Django's built-in auth app
    verbose_name = "Bible Authentication"
