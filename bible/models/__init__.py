"""
Bible models - centralized imports.
"""

from .auth import APIKey
from .books import Book, BookCategory, BookName, CanonicalBook, Language, License, Testament
from .crossrefs import CrossReference

# Commentary models - imported from dedicated domain
from bible.commentaries import (
    Author,
    CommentaryEntry,
    CommentaryEnrichment,
    CommentaryReference,
    CommentarySource,
    CommentaryTranslation,
    VerseComment,
)
from .nlp_cache import QueryNLPCache
from .query_expansion import QueryExpansionCache
from .rag import UnifiedThemeEmbedding, UnifiedVerseEmbedding, VerseEmbedding
from .themes import Theme, VerseTheme
from .topics import (
    Topic,
    TopicAspect,
    TopicAspectLabel,
    TopicContent,
    TopicCrossReference,
    TopicDefinition,
    TopicName,
    TopicPipelineMetadata,
    TopicRelation,
    TopicThemeLink,
    TopicVerse,
)
from .verses import Verse
from .versions import Version

# NOTE: Entity and Symbol models are in separate apps (bible.entities, bible.symbols)
# Import them directly from those apps to avoid circular imports:
#   from bible.entities import CanonicalEntity, EntityAlias, EntityRole, ...
#   from bible.symbols import BiblicalSymbol, SymbolMeaning, ...

__all__ = [
    # Legacy models (backward compatibility)
    "Book",
    "Verse",
    "Version",
    # New blueprint models
    "CanonicalBook",
    "BookName",
    "BookCategory",
    "Language",
    "License",
    "Testament",
    # Commentary models (from bible.commentaries domain)
    "Author",
    "CommentarySource",
    "CommentaryEntry",
    "CommentaryTranslation",
    "CommentaryEnrichment",
    "CommentaryReference",
    "VerseComment",
    # Other models
    "APIKey",
    "Theme",
    "VerseTheme",
    "CrossReference",
    "VerseEmbedding",
    "UnifiedVerseEmbedding",
    "UnifiedThemeEmbedding",
    # Query Expansion
    "QueryExpansionCache",
    # NLP Cache
    "QueryNLPCache",
    # Topic models
    "Topic",
    "TopicName",
    "TopicContent",
    "TopicDefinition",
    "TopicAspect",
    "TopicAspectLabel",
    "TopicVerse",
    "TopicThemeLink",
    "TopicCrossReference",
    "TopicRelation",
    "TopicPipelineMetadata",
    # NOTE: Entity and Symbol models are in separate apps
    # Import directly: from bible.entities import CanonicalEntity
    # Import directly: from bible.symbols import BiblicalSymbol
]
