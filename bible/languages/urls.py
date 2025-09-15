"""
URL configuration for Languages domain.
"""
from django.urls import path

from .views import LanguageListView

app_name = "languages"

urlpatterns = [
    path("", LanguageListView.as_view(), name="languages_list"),
]
