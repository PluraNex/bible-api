"""
Themes domain - Biblical themes with rich metadata and progression.

This domain manages biblical themes (concepts that span Scripture):
- Theme: Core theme with multilingual support and theological classification
- ThemeCategory: Hierarchical categorization
- ThemeProgression: How themes develop through biblical narrative
- ThemeVerseLink: Rich verse associations with context

Import models after Django apps are loaded:
    from bible.themes.models import Theme, ThemeProgression, ...
"""


def get_models():
    """Lazy import to avoid AppRegistryNotReady errors."""
    from .models import (
        Theme,
        ThemeCategory,
        ThemeProgression,
        ThemeRelatedTheme,
        ThemeVerseLink,
    )

    return {
        "Theme": Theme,
        "ThemeCategory": ThemeCategory,
        "ThemeProgression": ThemeProgression,
        "ThemeVerseLink": ThemeVerseLink,
        "ThemeRelatedTheme": ThemeRelatedTheme,
    }


__all__ = [
    "get_models",
    "Theme",
    "ThemeCategory",
    "ThemeProgression",
    "ThemeVerseLink",
    "ThemeRelatedTheme",
]


def __getattr__(name):
    """Lazy attribute access for model classes."""
    models = get_models()
    if name in models:
        return models[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")