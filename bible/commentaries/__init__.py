"""
Commentary domain - Biblical commentaries with AI enrichment.

This domain handles commentary sources, entries, translations, and enrichment
from Church Fathers to modern scholars.
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name in (
        "Author",
        "CommentarySource",
        "CommentaryEntry",
        "CommentaryTranslation",
        "CommentaryEnrichment",
        "CommentaryReference",
        "VerseComment",
    ):
        from bible.commentaries.models import (
            Author,
            CommentarySource,
            CommentaryEntry,
            CommentaryTranslation,
            CommentaryEnrichment,
            CommentaryReference,
            VerseComment,
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Author",
    "CommentarySource",
    "CommentaryEntry",
    "CommentaryTranslation",
    "CommentaryEnrichment",
    "CommentaryReference",
    "VerseComment",
]
