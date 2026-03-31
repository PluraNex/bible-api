"""
Theology app configuration.
"""

from django.apps import AppConfig


class TheologyConfig(AppConfig):
    """Configuration for the Theology domain app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.theology"
    label = "theology"
    verbose_name = "Systematic Theology"
