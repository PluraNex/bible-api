"""
URL configuration for Bible app.
"""
from django.urls import include, path

from . import views

app_name = "bible"

urlpatterns = [
    # Overview
    path("overview/", views.BibleOverviewAPIView.as_view(), name="overview"),
    # Domain includes
    path("books/", include(("bible.books.urls", "books"), namespace="books")),
    path("verses/", include(("bible.verses.urls", "verses"), namespace="verses")),
    path("themes/", include(("bible.themes.urls", "themes"), namespace="themes")),
    path("cross-references/", include(("bible.crossrefs.urls", "crossrefs"), namespace="crossrefs")),
    path("versions/", include(("bible.versions.urls", "versions"), namespace="versions")),
    path("languages/", include(("bible.languages.urls", "languages"), namespace="languages")),
    path("references/", include(("bible.references.urls", "references"), namespace="references")),
    path("rag/", include(("bible.rag.urls", "rag"), namespace="rag")),
]
