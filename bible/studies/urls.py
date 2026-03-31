"""URL configuration for the studies domain."""

from django.urls import path

from . import views

app_name = "studies"

urlpatterns = [
    # List & Create
    path("", views.StudyListView.as_view(), name="list"),
    path("create/", views.StudyCreateView.as_view(), name="create"),
    # Special listings
    path("bookmarked/", views.StudyBookmarkedListView.as_view(), name="bookmarked"),
    path("featured/", views.StudyFeaturedListView.as_view(), name="featured"),
    # Detail, Update, Delete
    path("<slug:slug>/", views.StudyDetailView.as_view(), name="detail"),
    # Rail preview
    path("<slug:slug>/rail/", views.StudyRailView.as_view(), name="rail"),
    # Actions
    path("<slug:slug>/publish/", views.StudyPublishView.as_view(), name="publish"),
    path("<slug:slug>/unpublish/", views.StudyUnpublishView.as_view(), name="unpublish"),
    path("<slug:slug>/fork/", views.StudyForkView.as_view(), name="fork"),
    path("<slug:slug>/bookmark/", views.StudyBookmarkView.as_view(), name="bookmark"),
]
