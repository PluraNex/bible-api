"""Views for themes domain."""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from common.openapi import LANG_PARAMETER, get_error_responses

from ..models import CanonicalBook, Theme, VerseTheme
from .serializers import (
    ConceptMapSerializer,
    ThemeAnalysisByBookSerializer,
    ThemeProgressionSerializer,
    ThemeSerializer,
    ThemeStatisticsSerializer,
)


class ThemeListView(generics.ListAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    @extend_schema(
        summary="List themes",
        tags=["themes"],
        responses={
            200: ThemeSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ThemeDetailView(generics.RetrieveAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    lookup_field = "pk"

    @extend_schema(
        summary="Get theme detail",
        tags=["themes"],
        responses={
            200: ThemeSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ThemeSearchView(generics.ListAPIView):
    """Search themes by name and description."""

    serializer_class = ThemeSerializer

    @extend_schema(
        summary="Search themes by text",
        description="Search themes by name and description using full-text search",
        tags=["themes"],
        parameters=[
            OpenApiParameter(
                name="q",
                description="Search query for theme name and description",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="limit",
                description="Limit number of results (default: 20)",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: ThemeSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": 'Query parameter "q" is required.'}, status=400)

        limit = int(request.query_params.get("limit", 20))

        # Full-text search on name and description
        themes = (
            Theme.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
            .annotate(verse_count=Count("verse_links", distinct=True))
            .order_by("-verse_count", "name")[:limit]
        )

        serializer = self.get_serializer(themes, many=True)
        return Response(serializer.data)


class ThemeStatisticsView(APIView):
    """Get comprehensive statistics for a specific theme."""

    @extend_schema(
        summary="Get theme statistics",
        description="Get comprehensive metrics and statistics for a specific theme",
        tags=["themes"],
        parameters=[LANG_PARAMETER],
        responses={
            200: ThemeStatisticsSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, theme_id, *args, **kwargs):
        from bible.utils.i18n import mark_response_language_sensitive

        mark_response_language_sensitive(request)

        theme = get_object_or_404(Theme, id=theme_id)

        # Get basic counts
        verse_links = VerseTheme.objects.filter(theme=theme).select_related("verse__book", "verse__version")

        verse_count = verse_links.count()
        book_count = verse_links.values("verse__book").distinct().count()
        version_count = verse_links.values("verse__version").distinct().count()

        # Get top books with most verses for this theme
        top_books_data = (
            verse_links.values("verse__book__osis_code", "verse__book__canonical_order")
            .annotate(verse_count=Count("verse"))
            .order_by("-verse_count")[:10]
        )

        top_books = []
        for book_data in top_books_data:
            book = CanonicalBook.objects.get(osis_code=book_data["verse__book__osis_code"])
            lang_code = request.lang_code if hasattr(request, "lang_code") else "en"
            book_name = book.names.filter(language__code=lang_code, version__isnull=True).first()
            top_books.append(
                {
                    "osis_code": book_data["verse__book__osis_code"],
                    "name": book_name.name if book_name else book_data["verse__book__osis_code"],
                    "canonical_order": book_data["verse__book__canonical_order"],
                    "verse_count": book_data["verse_count"],
                }
            )

        # Testament distribution
        testament_distribution = {}
        for link in verse_links:
            testament_name = link.verse.book.testament.name
            testament_distribution[testament_name] = testament_distribution.get(testament_name, 0) + 1

        statistics_data = {
            "theme_id": theme.id,
            "theme_name": theme.name,
            "verse_count": verse_count,
            "book_count": book_count,
            "version_count": version_count,
            "top_books": top_books,
            "testament_distribution": testament_distribution,
        }

        serializer = ThemeStatisticsSerializer(data=statistics_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ThemeAnalysisByBookView(APIView):
    """Analyze theme distribution within a specific biblical book."""

    @extend_schema(
        summary="Analyze themes by book",
        description="Get detailed theme analysis for a specific biblical book",
        tags=["themes"],
        parameters=[LANG_PARAMETER],
        responses={
            200: ThemeAnalysisByBookSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, *args, **kwargs):
        from bible.utils.i18n import mark_response_language_sensitive

        mark_response_language_sensitive(request)

        # Find book by OSIS code or name
        book = None
        try:
            # Try OSIS code first
            book = CanonicalBook.objects.get(osis_code__iexact=book_name)
        except CanonicalBook.DoesNotExist:
            # Try by name in resolved language
            lang_code = request.lang_code if hasattr(request, "lang_code") else "en"
            book_name_obj = CanonicalBook.objects.filter(
                names__name__iexact=book_name, names__language__code=lang_code
            ).first()
            if book_name_obj:
                book = book_name_obj

        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

        # Get book name for display in resolved language
        lang_code = request.lang_code if hasattr(request, "lang_code") else "en"
        display_name = book.names.filter(language__code=lang_code, version__isnull=True).first()
        book_display_name = display_name.name if display_name else book.osis_code

        # Get all verse-theme associations for this book
        verse_themes = VerseTheme.objects.filter(verse__book=book).select_related("theme", "verse")

        # Count total verses in this book (across all versions)
        total_book_verses = book.verses.count()

        # Get themed verses count
        total_themed_verses = verse_themes.values("verse").distinct().count()

        # Calculate coverage percentage
        coverage_percentage = (total_themed_verses / total_book_verses * 100) if total_book_verses > 0 else 0.0

        # Theme distribution analysis
        theme_distribution = {}
        chapter_analysis = {}

        for vt in verse_themes:
            theme_name = vt.theme.name
            chapter = vt.verse.chapter

            # Theme distribution
            if theme_name not in theme_distribution:
                theme_distribution[theme_name] = {
                    "theme_id": vt.theme.id,
                    "theme_name": theme_name,
                    "verse_count": 0,
                    "chapters": set(),
                }
            theme_distribution[theme_name]["verse_count"] += 1
            theme_distribution[theme_name]["chapters"].add(chapter)

            # Chapter analysis
            if chapter not in chapter_analysis:
                chapter_analysis[chapter] = {"chapter": chapter, "themes": {}, "total_themed_verses": 0}

            if theme_name not in chapter_analysis[chapter]["themes"]:
                chapter_analysis[chapter]["themes"][theme_name] = 0
            chapter_analysis[chapter]["themes"][theme_name] += 1
            chapter_analysis[chapter]["total_themed_verses"] += 1

        # Format theme distribution for response
        theme_distribution_list = []
        for _theme_name, data in theme_distribution.items():
            theme_distribution_list.append(
                {
                    "theme_id": data["theme_id"],
                    "theme_name": data["theme_name"],
                    "verse_count": data["verse_count"],
                    "chapter_count": len(data["chapters"]),
                    "chapters": sorted(data["chapters"]),
                }
            )
        theme_distribution_list.sort(key=lambda x: x["verse_count"], reverse=True)

        # Format chapter analysis for response
        chapter_analysis_list = []
        for chapter, data in sorted(chapter_analysis.items()):
            chapter_analysis_list.append(
                {
                    "chapter": chapter,
                    "total_themed_verses": data["total_themed_verses"],
                    "theme_count": len(data["themes"]),
                    "themes": [{"theme": theme, "verse_count": count} for theme, count in data["themes"].items()],
                }
            )

        analysis_data = {
            "book_name": book_display_name,
            "book_osis_code": book.osis_code,
            "canonical_order": book.canonical_order,
            "theme_distribution": theme_distribution_list,
            "chapter_analysis": chapter_analysis_list,
            "total_themed_verses": total_themed_verses,
            "total_book_verses": total_book_verses,
            "coverage_percentage": round(coverage_percentage, 2),
        }

        serializer = ThemeAnalysisByBookSerializer(data=analysis_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ThemeProgressionView(APIView):
    """Show chronological progression of a theme through biblical canon."""

    @extend_schema(
        summary="Get theme chronological progression",
        description="Show how a theme develops chronologically through the biblical canon",
        tags=["themes"],
        parameters=[LANG_PARAMETER],
        responses={
            200: ThemeProgressionSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, theme_id, *args, **kwargs):
        from bible.utils.i18n import mark_response_language_sensitive

        mark_response_language_sensitive(request)

        theme = get_object_or_404(Theme, id=theme_id)

        # Get verse-theme associations ordered by canonical book order
        verse_themes = (
            VerseTheme.objects.filter(theme=theme)
            .select_related("verse__book", "verse__book__testament")
            .order_by("verse__book__canonical_order")
        )

        if not verse_themes.exists():
            return Response({"detail": f'No verses found for theme "{theme.name}".'}, status=404)

        # Group by book for progression analysis
        book_progression = {}
        testament_summary = {"OLD": {"book_count": 0, "verse_count": 0}, "NEW": {"book_count": 0, "verse_count": 0}}

        for vt in verse_themes:
            book = vt.verse.book
            testament_name = book.testament.name

            if book.osis_code not in book_progression:
                lang_code = request.lang_code if hasattr(request, "lang_code") else "en"
                book_name = book.names.filter(language__code=lang_code, version__isnull=True).first()
                book_progression[book.osis_code] = {
                    "osis_code": book.osis_code,
                    "name": book_name.name if book_name else book.osis_code,
                    "canonical_order": book.canonical_order,
                    "testament": testament_name,
                    "verse_count": 0,
                    "chapters": set(),
                    "first_occurrence": {"chapter": vt.verse.chapter, "verse": vt.verse.number},
                    "verses": [],
                }
                testament_summary[testament_name]["book_count"] += 1

            book_progression[book.osis_code]["verse_count"] += 1
            book_progression[book.osis_code]["chapters"].add(vt.verse.chapter)
            book_progression[book.osis_code]["verses"].append(
                {
                    "chapter": vt.verse.chapter,
                    "verse": vt.verse.number,
                    "text_preview": vt.verse.text[:100] + "..." if len(vt.verse.text) > 100 else vt.verse.text,
                }
            )
            testament_summary[testament_name]["verse_count"] += 1

        # Convert to list and sort by canonical order
        progression_data = []
        for book_data in sorted(book_progression.values(), key=lambda x: x["canonical_order"]):
            # Calculate chapter distribution
            chapters = sorted(book_data["chapters"])
            chapter_distribution = {}
            for verse in book_data["verses"]:
                chapter = verse["chapter"]
                if chapter not in chapter_distribution:
                    chapter_distribution[chapter] = 0
                chapter_distribution[chapter] += 1

            progression_data.append(
                {
                    "osis_code": book_data["osis_code"],
                    "name": book_data["name"],
                    "canonical_order": book_data["canonical_order"],
                    "testament": book_data["testament"],
                    "verse_count": book_data["verse_count"],
                    "chapter_count": len(chapters),
                    "chapters": chapters,
                    "first_occurrence": book_data["first_occurrence"],
                    "chapter_distribution": chapter_distribution,
                    "intensity": book_data["verse_count"],  # Could be normalized later
                }
            )

        # Calculate peak books (highest concentration)
        peak_books = sorted(progression_data, key=lambda x: x["verse_count"], reverse=True)[:5]

        # Format testament summary
        for testament in testament_summary:
            testament_summary[testament]["percentage"] = (
                round(
                    (
                        testament_summary[testament]["verse_count"]
                        / sum(t["verse_count"] for t in testament_summary.values())
                        * 100
                    ),
                    2,
                )
                if sum(t["verse_count"] for t in testament_summary.values()) > 0
                else 0
            )

        progression_response_data = {
            "theme_id": theme.id,
            "theme_name": theme.name,
            "progression_data": progression_data,
            "testament_summary": testament_summary,
            "peak_books": [
                {
                    "osis_code": book["osis_code"],
                    "name": book["name"],
                    "testament": book["testament"],
                    "verse_count": book["verse_count"],
                    "intensity_rank": idx + 1,
                }
                for idx, book in enumerate(peak_books)
            ],
        }

        serializer = ThemeProgressionSerializer(data=progression_response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ConceptMapView(APIView):
    """Generate concept relationship map for themes based on co-occurrence."""

    @extend_schema(
        summary="Get concept relationship map",
        description="Generate theme relationship map based on verse co-occurrence patterns",
        tags=["themes"],
        responses={
            200: ConceptMapSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, concept, *args, **kwargs):
        # Find the main theme by name (case-insensitive)
        main_theme = Theme.objects.filter(name__icontains=concept).first()

        if not main_theme:
            return Response({"detail": f'No theme found matching concept "{concept}".'}, status=404)

        # Get all verses associated with the main theme
        main_theme_verses = set(VerseTheme.objects.filter(theme=main_theme).values_list("verse_id", flat=True))

        if not main_theme_verses:
            return Response({"detail": f'No verses found for theme "{main_theme.name}".'}, status=404)

        # Find co-occurring themes (themes that appear in the same verses)
        co_occurring_themes = {}

        # Get all theme-verse associations for verses that contain the main theme
        related_verse_themes = (
            VerseTheme.objects.filter(verse_id__in=main_theme_verses)
            .exclude(theme=main_theme)
            .select_related("theme", "verse")
        )

        for vt in related_verse_themes:
            theme_name = vt.theme.name
            if theme_name not in co_occurring_themes:
                co_occurring_themes[theme_name] = {
                    "theme_id": vt.theme.id,
                    "theme_name": theme_name,
                    "co_occurrence_count": 0,
                    "shared_verses": set(),
                    "strength": 0.0,
                }

            co_occurring_themes[theme_name]["co_occurrence_count"] += 1
            co_occurring_themes[theme_name]["shared_verses"].add(vt.verse_id)

        # Calculate relationship strength and format co-occurrence data
        total_main_theme_verses = len(main_theme_verses)
        co_occurrence_data = []

        for _theme_name, data in co_occurring_themes.items():
            # Strength based on percentage of shared verses
            strength = len(data["shared_verses"]) / total_main_theme_verses
            data["strength"] = round(strength, 3)

            co_occurrence_data.append(
                {
                    "theme_id": data["theme_id"],
                    "theme_name": data["theme_name"],
                    "co_occurrence_count": data["co_occurrence_count"],
                    "shared_verse_count": len(data["shared_verses"]),
                    "strength": data["strength"],
                    "relationship_type": self._categorize_relationship(data["strength"]),
                }
            )

        # Sort by strength (strongest relationships first)
        co_occurrence_data.sort(key=lambda x: x["strength"], reverse=True)

        # Get top related themes (limit to avoid overwhelming response)
        related_themes = co_occurrence_data[:15]

        # Calculate overall strength metrics
        if co_occurrence_data:
            max_strength = max(item["strength"] for item in co_occurrence_data)
            avg_strength = sum(item["strength"] for item in co_occurrence_data) / len(co_occurrence_data)
            strong_relationships = len([item for item in co_occurrence_data if item["strength"] > 0.1])
        else:
            max_strength = avg_strength = strong_relationships = 0

        strength_metrics = {
            "total_related_themes": len(co_occurrence_data),
            "strong_relationships_count": strong_relationships,
            "max_relationship_strength": round(max_strength, 3),
            "average_relationship_strength": round(avg_strength, 3),
            "main_theme_verse_count": total_main_theme_verses,
        }

        # Get example verses showing concept relationships
        verse_examples = []
        if related_themes:
            # Get verses that contain the main theme and the strongest related theme
            strongest_related_theme_id = related_themes[0]["theme_id"]
            example_verse_ids = list(
                VerseTheme.objects.filter(
                    verse_id__in=main_theme_verses, theme_id=strongest_related_theme_id
                ).values_list("verse_id", flat=True)[:3]
            )

            for verse_id in example_verse_ids:
                verse = VerseTheme.objects.filter(verse_id=verse_id).first().verse
                related_theme_names = [vt.theme.name for vt in VerseTheme.objects.filter(verse_id=verse_id)]

                verse_examples.append(
                    {
                        "verse_id": verse_id,
                        "reference": verse.reference,
                        "text_preview": verse.text[:150] + "..." if len(verse.text) > 150 else verse.text,
                        "related_themes": related_theme_names,
                    }
                )

        concept_map_data = {
            "concept": main_theme.name,
            "related_themes": related_themes,
            "co_occurrence_data": co_occurrence_data,
            "strength_metrics": strength_metrics,
            "verse_examples": verse_examples,
        }

        serializer = ConceptMapSerializer(data=concept_map_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def _categorize_relationship(self, strength):
        """Categorize relationship strength into descriptive labels."""
        if strength >= 0.3:
            return "very_strong"
        elif strength >= 0.15:
            return "strong"
        elif strength >= 0.05:
            return "moderate"
        else:
            return "weak"
