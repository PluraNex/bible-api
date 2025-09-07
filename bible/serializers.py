"""
Aggregated imports for serializers (backward-compat).
Prefer importing from domain modules: books/verses/themes/crossrefs.
"""

from .books.serializers import BookSerializer  # noqa: F401
from .crossrefs.serializers import CrossReferenceSerializer  # noqa: F401
from .themes.serializers import ThemeSerializer  # noqa: F401
from .verses.serializers import VerseSerializer  # noqa: F401
