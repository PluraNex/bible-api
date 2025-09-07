"""
URL configuration for Themes domain.
"""
from django.urls import path

from .views import ThemeDetailView, ThemeListView

app_name = "themes"

urlpatterns = [
    path("", ThemeListView.as_view(), name="themes_list"),
    path("<int:pk>/detail/", ThemeDetailView.as_view(), name="theme_detail"),
]
