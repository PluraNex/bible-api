"""
Themes app configuration.
"""

from django.apps import AppConfig


class ThemesConfig(AppConfig):
    """Configuration for the Themes domain app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.themes"
    label = "themes"
    verbose_name = "Biblical Themes"
