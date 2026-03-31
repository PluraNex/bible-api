"""Views for topics domain."""

from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import build_error_response
from common.mixins import LanguageSensitiveMixin
from common.openapi import LANG_PARAMETER, get_error_responses
from common.pagination import StandardResultsSetPagination

from ..models import (
    Topic,
    TopicAspect,
    TopicCrossReference,
    TopicDefinition,
    TopicRelation,
    TopicThemeLink,
)
from .serializers import (
    TopicAspectSerializer,
    TopicCrossReferenceSerializer,
    TopicDefinitionSerializer,
    TopicDetailSerializer,
    TopicListSerializer,
    TopicRelationSerializer,
    TopicSearchResultSerializer,
    TopicStatisticsSerializer,
    TopicThemeLinkSerializer,
)


def get_topic_queryset():
    """
    Optimized queryset with select_related and prefetch_related.
    Avoids N+1 queries.
    
    Note: Cannot use slicing in Prefetch as it breaks filtering.
    Slicing should be done in serializers instead.
    """
    return Topic.objects.prefetch_related(
        "names",
        "names__language",
        "contents",
        "contents__language",
        Prefetch("definitions", queryset=TopicDefinition.objects.order_by("source")),
        Prefetch("aspects", queryset=TopicAspect.objects.order_by("order")),
        Prefetch(
            "theme_links",
            queryset=TopicThemeLink.objects.select_related("theme").order_by("-relevance_score"),
        ),
    )


class TopicListView(LanguageSensitiveMixin, generics.ListAPIView):
    """List all topics with pagination and filtering."""

    serializer_class = TopicListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get topics with optional filters."""
        queryset = Topic.objects.prefetch_related("names", "names__language").order_by("name_normalized")

        # Filter by type
        topic_type = self.request.query_params.get("type")
        if topic_type:
            queryset = queryset.filter(topic_type=topic_type)

        # Filter by source
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(primary_source=source.upper())

        # Filter by AI enriched
        ai_enriched = self.request.query_params.get("ai_enriched")
        if ai_enriched is not None:
            queryset = queryset.filter(ai_enriched=ai_enriched.lower() == "true")

        # Filter by letter
        letter = self.request.query_params.get("letter")
        if letter:
            queryset = queryset.filter(name_normalized__istartswith=letter.lower())

        return queryset

    @extend_schema(
        summary="List topics",
        description="Get a paginated list of biblical topics/encyclopedia entries.",
        tags=["topics"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="type",
                description="Filter by topic type (person, place, concept, event, object, literary)",
                required=False,
            ),
            OpenApiParameter(
                name="source",
                description="Filter by primary source (NAV, TOR, etc.)",
                required=False,
            ),
            OpenApiParameter(
                name="ai_enriched",
                description="Filter by AI enrichment status (true/false)",
                required=False,
            ),
            OpenApiParameter(
                name="letter",
                description="Filter by starting letter",
                required=False,
            ),
        ],
        responses={
            200: TopicListSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        """Add request context for language resolution."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class TopicDetailView(LanguageSensitiveMixin, APIView):
    """Get detailed information about a specific topic."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get topic detail",
        description="Retrieve comprehensive information about a specific biblical topic.",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TopicDetailSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "Get Abraham topic",
                value={"slug": "abraham"},
                request_only=True,
            ),
        ],
    )
    def get(self, request, slug):
        try:
            topic = get_topic_queryset().get(slug=slug)
            serializer = TopicDetailSerializer(topic, context={"request": request})
            return Response(serializer.data)
        except Topic.DoesNotExist:
            return build_error_response(
                f'Topic "{slug}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class TopicSearchView(LanguageSensitiveMixin, generics.GenericAPIView):
    """Search topics by name, alias, or content."""

    serializer_class = TopicSearchResultSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Search topics",
        description="Search topics by name, alias, or content with multilingual support.",
        tags=["topics"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="q",
                description="Search query",
                required=True,
            ),
            OpenApiParameter(
                name="type",
                description="Filter by topic type",
                required=False,
            ),
        ],
        responses={
            200: TopicSearchResultSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query:
            return build_error_response(
                'Query parameter "q" is required.',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        topic_type = request.query_params.get("type")
        lang_code = getattr(request, "lang_code", "en")

        # Search in canonical name and normalized name
        name_query = Q(canonical_name__icontains=query) | Q(name_normalized__icontains=query)

        # Search in localized names
        name_query |= Q(names__name__icontains=query)

        # Search in aliases
        name_query |= Q(names__aliases__icontains=query)

        # Search in content
        content_query = Q(contents__summary__icontains=query)

        topics = (
            Topic.objects.filter(name_query | content_query)
            .prefetch_related("names", "contents")
            .distinct()
            .order_by("-total_verses", "name_normalized")
        )

        if topic_type:
            topics = topics.filter(topic_type=topic_type)

        # Format results
        results = []
        added_slugs = set()

        for topic in topics[:50]:  # Limit results
            if topic.slug in added_slugs:
                continue
            added_slugs.add(topic.slug)

            # Get summary preview
            content = topic.contents.filter(language__code=lang_code).first()
            if not content:
                content = topic.contents.filter(language__code="en").first()

            summary_preview = ""
            if content and content.summary:
                summary_preview = content.summary[:150] + "..." if len(content.summary) > 150 else content.summary

            # Determine match type
            match_type = "name"
            if query.lower() in topic.name_normalized:
                match_type = "name"
            elif topic.names.filter(aliases__icontains=query).exists():
                match_type = "alias"
            else:
                match_type = "content"

            results.append(
                {
                    "slug": topic.slug,
                    "name": topic.get_display_name(lang_code),
                    "topic_type": topic.topic_type,
                    "summary_preview": summary_preview,
                    "total_verses": topic.total_verses,
                    "match_type": match_type,
                    "match_score": 1.0 if match_type == "name" else 0.8 if match_type == "alias" else 0.6,
                }
            )

        # Sort by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)

        page = self.paginate_queryset(results)
        serializer = self.get_serializer(page if page is not None else results, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class TopicAspectsView(LanguageSensitiveMixin, generics.ListAPIView):
    """List all aspects/subtopics for a topic."""

    serializer_class = TopicAspectSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return (
            TopicAspect.objects.filter(topic__slug=slug)
            .prefetch_related("labels", "labels__language")
            .order_by("order")
        )

    @extend_schema(
        summary="List topic aspects",
        description="Get all structured aspects/subtopics within a biblical topic.",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TopicAspectSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class TopicDefinitionsView(LanguageSensitiveMixin, generics.ListAPIView):
    """List all dictionary definitions for a topic."""

    serializer_class = TopicDefinitionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return TopicDefinition.objects.filter(topic__slug=slug).order_by("source")

    @extend_schema(
        summary="List topic definitions",
        description="Get dictionary definitions from various sources (EAS, SMI, NAV, etc.).",
        tags=["topics"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="source",
                description="Filter by source (EAS, SMI, NAV, TOR, etc.)",
                required=False,
            ),
        ],
        responses={
            200: TopicDefinitionSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        source = request.query_params.get("source")
        queryset = self.get_queryset()

        if source:
            queryset = queryset.filter(source=source.upper())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TopicThemesView(LanguageSensitiveMixin, generics.ListAPIView):
    """List all themes extracted for a topic."""

    serializer_class = TopicThemeLinkSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return (
            TopicThemeLink.objects.filter(topic__slug=slug)
            .select_related("theme")
            .order_by("-relevance_score")
        )

    @extend_schema(
        summary="List topic themes",
        description="Get AI-extracted themes with anchor verses and metadata.",
        tags=["topics"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="domain",
                description="Filter by theological domain",
                required=False,
            ),
        ],
        responses={
            200: TopicThemeLinkSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get(self, request, *args, **kwargs):
        domain = request.query_params.get("domain")
        queryset = self.get_queryset()

        if domain:
            queryset = queryset.filter(theological_domain=domain)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TopicCrossReferencesView(LanguageSensitiveMixin, generics.ListAPIView):
    """List cross-references for a topic."""

    serializer_class = TopicCrossReferenceSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return (
            TopicCrossReference.objects.filter(topic__slug=slug)
            .select_related("cross_reference", "cross_reference__from_book", "cross_reference__to_book")
            .order_by("-relevance_score", "cross_reference__from_book", "cross_reference__from_chapter", "cross_reference__from_verse")
        )

    @extend_schema(
        summary="List topic cross-references",
        description="Get cross-reference network from TSK data.",
        tags=["topics"],
        parameters=[
            OpenApiParameter(
                name="strength",
                description="Filter by strength (strong, moderate, weak)",
                required=False,
            ),
            OpenApiParameter(
                name="from_verse",
                description="Filter by source verse reference",
                required=False,
            ),
        ],
        responses={
            200: TopicCrossReferenceSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        strength = request.query_params.get("strength")
        from_verse = request.query_params.get("from_verse")
        queryset = self.get_queryset()

        if strength:
            queryset = queryset.filter(cross_reference__strength=strength)
        if from_verse:
            # Search in book name or chapter/verse
            queryset = queryset.filter(cross_reference__from_book__name__icontains=from_verse)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class TopicRelatedView(LanguageSensitiveMixin, generics.ListAPIView):
    """List related topics."""

    serializer_class = TopicRelationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        return (
            TopicRelation.objects.filter(source__slug=slug)
            .select_related("target")
            .prefetch_related("target__names", "target__names__language")
        )

    @extend_schema(
        summary="List related topics",
        description="Get topics related to this one (see_also, parent, child, etc.).",
        tags=["topics"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="relation_type",
                description="Filter by relation type (see_also, related, parent, child, alias)",
                required=False,
            ),
        ],
        responses={
            200: TopicRelationSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get(self, request, *args, **kwargs):
        relation_type = request.query_params.get("relation_type")
        queryset = self.get_queryset()

        if relation_type:
            queryset = queryset.filter(relation_type=relation_type)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TopicStatisticsView(LanguageSensitiveMixin, APIView):
    """Get comprehensive statistics for a topic."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get topic statistics",
        description="Get comprehensive metrics and statistics for a specific topic.",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TopicStatisticsSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, slug):
        try:
            topic = Topic.objects.prefetch_related(
                "definitions",
                "theme_links",
                "cross_references",
                "aspects",
            ).get(slug=slug)
        except Topic.DoesNotExist:
            return build_error_response(
                f'Topic "{slug}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        lang_code = getattr(request, "lang_code", "en")

        # Calculate statistics
        definitions_count = topic.definitions.count()
        themes_count = topic.theme_links.count()
        cross_references_count = topic.cross_references.count()

        # Testament distribution
        testament_distribution = {
            "Old Testament": topic.ot_refs,
            "New Testament": topic.nt_refs,
        }

        # Top books (from aspects)
        top_books = []
        books_from_aspects = {}
        for aspect in topic.aspects.all():
            for book_code in aspect.books:
                books_from_aspects[book_code] = books_from_aspects.get(book_code, 0) + aspect.verse_count

        for book_code, verse_count in sorted(books_from_aspects.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_books.append(
                {
                    "osis_code": book_code,
                    "verse_count": verse_count,
                }
            )

        statistics_data = {
            "topic_slug": topic.slug,
            "topic_name": topic.get_display_name(lang_code),
            "topic_type": topic.topic_type,
            "total_verses": topic.total_verses,
            "ot_refs": topic.ot_refs,
            "nt_refs": topic.nt_refs,
            "books_count": topic.books_count,
            "aspects_count": topic.aspects_count,
            "definitions_count": definitions_count,
            "themes_count": themes_count,
            "cross_references_count": cross_references_count,
            "testament_distribution": testament_distribution,
            "top_books": top_books,
        }

        serializer = TopicStatisticsSerializer(data=statistics_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class TopicsByLetterView(LanguageSensitiveMixin, generics.ListAPIView):
    """List topics grouped by starting letter."""

    serializer_class = TopicListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        letter = self.kwargs.get("letter", "").lower()
        return (
            Topic.objects.filter(name_normalized__istartswith=letter)
            .prefetch_related("names", "names__language")
            .order_by("name_normalized")
        )

    @extend_schema(
        summary="List topics by letter",
        description="Get all topics starting with a specific letter.",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TopicListSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class TopicsByTypeView(LanguageSensitiveMixin, generics.ListAPIView):
    """List topics by type (person, place, concept, etc.)."""

    serializer_class = TopicListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        topic_type = self.kwargs.get("topic_type", "").lower()
        return (
            Topic.objects.filter(topic_type=topic_type)
            .prefetch_related("names", "names__language")
            .order_by("name_normalized")
        )

    @extend_schema(
        summary="List topics by type",
        description="Get all topics of a specific type (person, place, concept, event, object, literary).",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TopicListSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class TopicAnchorVersesView(LanguageSensitiveMixin, APIView):
    """Get anchor verses for a topic's themes."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get topic anchor verses",
        description="Get key anchor verses from all themes linked to this topic.",
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "topic_slug": {"type": "string"},
                    "topic_name": {"type": "string"},
                    "anchor_verses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "reference": {"type": "string"},
                                "theme_label": {"type": "string"},
                                "relevance_score": {"type": "number"},
                            },
                        },
                    },
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, slug):
        try:
            topic = Topic.objects.prefetch_related("theme_links").get(slug=slug)
        except Topic.DoesNotExist:
            return build_error_response(
                f'Topic "{slug}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        lang_code = getattr(request, "lang_code", "en")

        anchor_verses = []
        for link in topic.theme_links.all().order_by("-relevance_score"):
            label = link.label_original if lang_code.startswith("pt") else link.label_en
            for verse_ref in link.anchor_verses:
                anchor_verses.append(
                    {
                        "reference": verse_ref,
                        "theme_label": label or link.label_normalized,
                        "relevance_score": link.relevance_score,
                    }
                )

        return Response(
            {
                "topic_slug": topic.slug,
                "topic_name": topic.get_display_name(lang_code),
                "anchor_verses": anchor_verses,
            }
        )


class TopicStudyView(LanguageSensitiveMixin, APIView):
    """
    Compose a rich study payload for a topic.

    Aggregates data from multiple sources: anchor verses, cross-references,
    commentaries, themes, entities, symbols, and related topics into a single
    response designed for deep study experiences.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get composed study for topic",
        description=(
            "Returns a rich study payload aggregating anchor verses, "
            "cross-reference networks, patristic commentaries, themes, "
            "entities, and symbols for deep biblical study."
        ),
        tags=["topics"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "meta": {"type": "object"},
                    "gold_references": {"type": "array"},
                    "connections": {"type": "object"},
                    "commentaries": {"type": "array"},
                    "aspects": {"type": "array"},
                    "themes": {"type": "array"},
                    "entities": {"type": "array"},
                    "symbols": {"type": "array"},
                    "related_topics": {"type": "array"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, slug):
        try:
            topic = get_topic_queryset().get(slug=slug)
        except Topic.DoesNotExist:
            return build_error_response(
                f'Topic "{slug}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        lang_code = getattr(request, "lang_code", "pt")

        from .services.study_composer import StudyComposer

        composer = StudyComposer(topic, lang_code=lang_code)
        payload = composer.compose()

        return Response(payload)
