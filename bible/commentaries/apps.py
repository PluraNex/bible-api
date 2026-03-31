"""Commentary domain app configuration."""

from django.apps import AppConfig


class CommentariesConfig(AppConfig):
    """Configuration for the commentaries domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.commentaries"
    label = "commentaries"
    verbose_name = "Biblical Commentaries"

    def ready(self):
        """Import signals and perform app initialization."""
        pass
