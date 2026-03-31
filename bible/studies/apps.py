"""Studies domain app configuration."""

from django.apps import AppConfig


class StudiesConfig(AppConfig):
    """Configuration for the studies domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.studies"
    label = "studies"
    verbose_name = "Biblical Studies"

    def ready(self):
        """Import signals and perform app initialization."""
        pass
