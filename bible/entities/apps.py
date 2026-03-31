"""
Entities app configuration.
"""

from django.apps import AppConfig


class EntitiesConfig(AppConfig):
    """Configuration for the Entities domain app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bible.entities"
    label = "entities"
    verbose_name = "Biblical Entities"
