"""
Bible models - centralized imports.
"""
from .auth import APIKey
from .books import Book, BookName, CanonicalBook, Language, License, Testament
from .comments import Author, CommentaryEntry, CommentarySource, VerseComment
from .crossrefs import CrossReference
from .rag import VerseEmbedding
from .themes import Theme, VerseTheme
from .verses import Verse
from .versions import Version

__all__ = [
    # Legacy models (backward compatibility)
    "Book",
    "Verse",
    "Version",
    # New blueprint models
    "CanonicalBook",
    "BookName",
    "Language",
    "License",
    "Testament",
    # Commentary models
    "Author",
    "CommentarySource",
    "CommentaryEntry",
    "VerseComment",
    # Other models
    "APIKey",
    "Theme",
    "VerseTheme",
    "CrossReference",
    "VerseEmbedding",
]
