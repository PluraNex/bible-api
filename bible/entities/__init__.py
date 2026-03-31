"""
Entities domain - Biblical entities with temporal roles and relationships.

This domain manages canonical biblical entities (people, places, concepts, etc.)
with support for:
- Multiple roles/functions over time (David: shepherd → king → prophet)
- Multilingual aliases (David, Davi, דָּוִד, Δαβίδ)
- Timeline events
- Verse associations with context
- Entity-to-entity relationships

Import models after Django apps are loaded:
    from bible.entities.models import CanonicalEntity, EntityAlias, ...
"""


def get_models():
    """Lazy import to avoid AppRegistryNotReady errors."""
    from .models import (
        CanonicalEntity,
        EntityAlias,
        EntityCategory,
        EntityCategoryLink,
        EntityRelationship,
        EntityRole,
        EntityTimeline,
        EntityVerseLink,
    )

    return {
        "CanonicalEntity": CanonicalEntity,
        "EntityAlias": EntityAlias,
        "EntityRole": EntityRole,
        "EntityTimeline": EntityTimeline,
        "EntityCategory": EntityCategory,
        "EntityCategoryLink": EntityCategoryLink,
        "EntityVerseLink": EntityVerseLink,
        "EntityRelationship": EntityRelationship,
    }


__all__ = [
    "get_models",
    "CanonicalEntity",
    "EntityAlias",
    "EntityRole",
    "EntityTimeline",
    "EntityCategory",
    "EntityCategoryLink",
    "EntityVerseLink",
    "EntityRelationship",
]


def __getattr__(name):
    """Lazy attribute access for model classes."""
    models = get_models()
    if name in models:
        return models[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
