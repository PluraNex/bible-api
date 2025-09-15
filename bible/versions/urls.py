"""URL routes for versions domain."""
from django.urls import path

from . import views

app_name = "versions"

urlpatterns = [
    path("", views.VersionListView.as_view(), name="versions_list"),
    path("default/", views.VersionDefaultView.as_view(), name="version_default"),
    path("<str:abbreviation>/", views.VersionDetailView.as_view(), name="version_detail"),
]
