"""Views for the Person hub."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets

from .models import Person
from .serializers import PersonDetailSerializer, PersonListSerializer


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Unified Person identity hub.
    Lists people across all domains (biblical figures, commentary authors, etc.).
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["person_type"]
    search_fields = ["canonical_name", "description"]
    ordering_fields = ["canonical_name", "birth_year", "person_type"]
    ordering = ["canonical_name"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PersonDetailSerializer
        return PersonListSerializer

    def get_queryset(self):
        return Person.objects.all()

    @extend_schema(
        summary="List people",
        description="List all people in the system. Filter by person_type (biblical, author, mixed).",
        tags=["people"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get person detail",
        description="Full person detail with links to author and biblical profiles.",
        tags=["people"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
