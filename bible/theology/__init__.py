"""
Theology domain - Systematic theology classification and doctrine management.

This domain provides the theological framework for the entire Bible API:
- TheologicalDomain: The 10 loci of systematic theology
- Doctrine: Specific doctrines with multi-level explanations
- TheologicalPerspective: Different traditions (Reformed, Arminian, etc.)
- DoctrinePerspectiveView: How each tradition views each doctrine
- Confession: Historical creeds and confessions
- TheologicalQuestion: FAQ for theological questions

Import models after Django apps are loaded:
    from bible.theology.models import TheologicalDomain, Doctrine, ...
"""


def get_models():
    """Lazy import to avoid AppRegistryNotReady errors."""
    from .models import (
        Confession,
        ConfessionArticle,
        Doctrine,
        DoctrinePerspectiveView,
        DoctrineVerseLink,
        TheologicalDomain,
        TheologicalPerspective,
        TheologicalQuestion,
    )

    return {
        "TheologicalDomain": TheologicalDomain,
        "Doctrine": Doctrine,
        "TheologicalPerspective": TheologicalPerspective,
        "DoctrinePerspectiveView": DoctrinePerspectiveView,
        "Confession": Confession,
        "ConfessionArticle": ConfessionArticle,
        "TheologicalQuestion": TheologicalQuestion,
        "DoctrineVerseLink": DoctrineVerseLink,
    }


__all__ = [
    "get_models",
    "TheologicalDomain",
    "Doctrine",
    "TheologicalPerspective",
    "DoctrinePerspectiveView",
    "Confession",
    "ConfessionArticle",
    "TheologicalQuestion",
    "DoctrineVerseLink",
]


def __getattr__(name):
    """Lazy attribute access for model classes."""
    models = get_models()
    if name in models:
        return models[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
