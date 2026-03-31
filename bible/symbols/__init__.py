"""
Symbols domain - Biblical symbols with multiple meanings and progression.

This domain manages biblical symbols (water, fire, lamb, lion, etc.)
with support for:
- Multiple symbolic meanings (water = purification, life, judgment)
- Literal vs figurative interpretation
- Symbol progression across biblical narrative
- Verse occurrences with context

Import models after Django apps are loaded:
    from bible.symbols.models import BiblicalSymbol, SymbolMeaning, ...
"""


def get_models():
    """Lazy import to avoid AppRegistryNotReady errors."""
    from .models import (
        BiblicalSymbol,
        SymbolCategory,
        SymbolMeaning,
        SymbolOccurrence,
        SymbolProgression,
    )

    return {
        "BiblicalSymbol": BiblicalSymbol,
        "SymbolMeaning": SymbolMeaning,
        "SymbolOccurrence": SymbolOccurrence,
        "SymbolProgression": SymbolProgression,
        "SymbolCategory": SymbolCategory,
    }


__all__ = [
    "get_models",
    "BiblicalSymbol",
    "SymbolMeaning",
    "SymbolOccurrence",
    "SymbolProgression",
    "SymbolCategory",
]


def __getattr__(name):
    """Lazy attribute access for model classes."""
    models = get_models()
    if name in models:
        return models[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
