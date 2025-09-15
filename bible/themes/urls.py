"""
URL configuration for Themes domain.
"""
from django.urls import path

from .views import (
    ConceptMapView,
    ThemeAnalysisByBookView,
    ThemeDetailView,
    ThemeListView,
    ThemeProgressionView,
    ThemeSearchView,
    ThemeStatisticsView,
)

app_name = "themes"

urlpatterns = [
    path("", ThemeListView.as_view(), name="themes_list"),
    path("search/", ThemeSearchView.as_view(), name="themes_search"),
    path("<int:pk>/detail/", ThemeDetailView.as_view(), name="theme_detail"),
    path("<int:theme_id>/statistics/", ThemeStatisticsView.as_view(), name="theme_statistics"),
    path("analysis/by-book/<str:book_name>/", ThemeAnalysisByBookView.as_view(), name="theme_analysis_book"),
    path("<int:theme_id>/progression/", ThemeProgressionView.as_view(), name="theme_progression"),
    path("concept-map/<str:concept>/", ConceptMapView.as_view(), name="concept_map"),
]
