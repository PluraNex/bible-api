"""
Symbols app configuration.
"""

from django.apps import AppConfig


class SymbolsConfig(AppConfig):
    """Configuration for the Symbols domain app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.symbols"
    label = "symbols"
    verbose_name = "Biblical Symbols"
