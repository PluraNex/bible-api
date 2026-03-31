"""Views for the studies domain."""

import copy

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import build_error_response
from common.pagination import StandardResultsSetPagination

from .models import Study, StudyBookmark
from .serializers import (
    StudyCreateSerializer,
    StudyDetailSerializer,
    StudyListSerializer,
    StudyRailSerializer,
    StudyUpdateSerializer,
)


class StudyListView(generics.ListAPIView):
    """List studies with filtering."""

    serializer_class = StudyListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Study.objects.select_related("author", "forked_from")

        # Filter: my studies (requires auth)
        mine = self.request.query_params.get("mine")
        if mine and mine.lower() == "true" and self.request.user.is_authenticated:
            queryset = queryset.filter(author=self.request.user)
        else:
            # Public listing: only published public/community studies
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(
                    visibility__in=["public", "community"],
                    is_published=True,
                )
            else:
                # Authenticated: own studies + published public/community
                queryset = queryset.filter(
                    Q(author=self.request.user)
                    | Q(visibility__in=["public", "community"], is_published=True)
                )

        # Filter by type
        study_type = self.request.query_params.get("type")
        if study_type:
            queryset = queryset.filter(study_type=study_type)

        # Filter by visibility
        visibility = self.request.query_params.get("visibility")
        if visibility:
            queryset = queryset.filter(visibility=visibility)

        # Filter by difficulty
        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Search by title/description
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        # Filter by tag
        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        return queryset.order_by("-updated_at")

    @extend_schema(
        summary="List studies",
        description="Get a paginated list of biblical studies.",
        tags=["studies"],
        parameters=[
            OpenApiParameter(name="mine", description="Show only my studies (true/false)", required=False),
            OpenApiParameter(name="type", description="Filter by study type", required=False),
            OpenApiParameter(name="visibility", description="Filter by visibility (private/public/community)", required=False),
            OpenApiParameter(name="difficulty", description="Filter by difficulty level", required=False),
            OpenApiParameter(name="q", description="Search in title and description", required=False),
            OpenApiParameter(name="tag", description="Filter by tag", required=False),
        ],
        responses={200: StudyListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StudyCreateView(APIView):
    """Create a new study."""

    # TODO: restore IsAuthenticated when auth flow is ready
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Create study",
        description="Create a new biblical study. Blocks are validated per type.",
        tags=["studies"],
        request=StudyCreateSerializer,
        responses={201: StudyDetailSerializer},
    )
    def post(self, request):
        serializer = StudyCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        study = serializer.save()
        return Response(
            StudyDetailSerializer(study, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class StudyDetailView(APIView):
    """Get, update, or delete a study."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_study(self, slug, request):
        study = get_object_or_404(
            Study.objects.select_related("author", "forked_from", "source_topic"),
            slug=slug,
        )
        # Check access
        if study.visibility == "private" and study.author != request.user:
            return None
        if not study.is_published and study.author != request.user:
            return None
        return study

    @extend_schema(
        summary="Get study detail",
        description="Retrieve a study with all blocks for full page view.",
        tags=["studies"],
        responses={200: StudyDetailSerializer},
    )
    def get(self, request, slug):
        study = self._get_study(slug, request)
        if not study:
            return build_error_response(
                "Study not found",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND,
                request=request,
            )
        # Increment view count
        Study.objects.filter(pk=study.pk).update(view_count=study.view_count + 1)
        return Response(
            StudyDetailSerializer(study, context={"request": request}).data
        )

    @extend_schema(
        summary="Update study",
        description="Partially update a study (title, blocks, metadata).",
        tags=["studies"],
        request=StudyUpdateSerializer,
        responses={200: StudyDetailSerializer},
    )
    def patch(self, request, slug):
        study = get_object_or_404(Study, slug=slug, author=request.user)
        serializer = StudyUpdateSerializer(study, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            StudyDetailSerializer(study, context={"request": request}).data
        )

    @extend_schema(
        summary="Delete study",
        description="Delete a study. Only the author can delete.",
        tags=["studies"],
        responses={204: None},
    )
    def delete(self, request, slug):
        study = get_object_or_404(Study, slug=slug, author=request.user)
        study.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudyRailView(APIView):
    """Get compact study representation for the rail panel."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get study rail preview",
        description="Compact payload for the study rail panel — metadata + preview blocks.",
        tags=["studies"],
        responses={200: StudyRailSerializer},
    )
    def get(self, request, slug):
        study = get_object_or_404(
            Study.objects.select_related("author"),
            slug=slug,
        )
        if study.visibility == "private" and study.author != request.user:
            return build_error_response(
                "Study not found",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND,
                request=request,
            )
        return Response(
            StudyRailSerializer(study, context={"request": request}).data
        )


class StudyPublishView(APIView):
    """Publish or unpublish a study."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Publish study",
        description="Publish a study, making it visible based on its visibility setting.",
        tags=["studies"],
        responses={200: StudyDetailSerializer},
    )
    def post(self, request, slug):
        study = get_object_or_404(Study, slug=slug, author=request.user)
        study.is_published = True
        study.published_at = timezone.now()
        study.save(update_fields=["is_published", "published_at", "updated_at"])
        return Response(
            StudyDetailSerializer(study, context={"request": request}).data
        )


class StudyUnpublishView(APIView):
    """Unpublish a study."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Unpublish study",
        description="Unpublish a study, hiding it from public listings.",
        tags=["studies"],
        responses={200: StudyDetailSerializer},
    )
    def post(self, request, slug):
        study = get_object_or_404(Study, slug=slug, author=request.user)
        study.is_published = False
        study.save(update_fields=["is_published", "updated_at"])
        return Response(
            StudyDetailSerializer(study, context={"request": request}).data
        )


class StudyForkView(APIView):
    """Fork a public study into the user's private studies."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Fork study",
        description="Create a private copy of a public study.",
        tags=["studies"],
        responses={201: StudyDetailSerializer},
    )
    def post(self, request, slug):
        original = get_object_or_404(
            Study,
            slug=slug,
            visibility__in=["public", "community"],
            is_published=True,
        )

        # Create a deep copy of blocks
        new_blocks = copy.deepcopy(original.blocks)

        # Generate unique slug
        base_slug = slugify(original.title)[:170]
        fork_slug = f"{base_slug}-fork"
        counter = 1
        while Study.objects.filter(slug=fork_slug).exists():
            fork_slug = f"{base_slug}-fork-{counter}"
            counter += 1

        forked = Study.objects.create(
            slug=fork_slug,
            title=original.title,
            subtitle=original.subtitle,
            author=request.user,
            study_type=original.study_type,
            difficulty=original.difficulty,
            visibility="private",
            blocks=new_blocks,
            description=original.description,
            tags=list(original.tags),
            language=original.language,
            forked_from=original,
        )

        # Increment fork count on original
        Study.objects.filter(pk=original.pk).update(
            fork_count=original.fork_count + 1
        )

        return Response(
            StudyDetailSerializer(forked, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class StudyBookmarkView(APIView):
    """Toggle bookmark on a study."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Toggle study bookmark",
        description="Bookmark or unbookmark a study.",
        tags=["studies"],
        responses={200: {"type": "object", "properties": {"bookmarked": {"type": "boolean"}}}},
    )
    def post(self, request, slug):
        study = get_object_or_404(Study, slug=slug)
        bookmark, created = StudyBookmark.objects.get_or_create(
            study=study, user=request.user
        )
        if not created:
            bookmark.delete()
        return Response({"bookmarked": created})


class StudyBookmarkedListView(generics.ListAPIView):
    """List user's bookmarked studies."""

    serializer_class = StudyListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Study.objects.filter(
            bookmarks__user=self.request.user
        ).select_related("author").order_by("-bookmarks__created_at")

    @extend_schema(
        summary="List bookmarked studies",
        description="Get the current user's bookmarked studies.",
        tags=["studies"],
        responses={200: StudyListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StudyFeaturedListView(generics.ListAPIView):
    """List featured/curated studies."""

    serializer_class = StudyListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Study.objects.filter(
            is_published=True,
            visibility="public",
            source_validation_id__gt="",
        ).select_related("author").order_by("-view_count")

    @extend_schema(
        summary="List featured studies",
        description="Get curated/featured studies (seeded from validation data).",
        tags=["studies"],
        responses={200: StudyListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
