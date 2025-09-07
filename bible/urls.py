"""
URL configuration for Bible app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "bible"

router = DefaultRouter()

urlpatterns = [
    path("overview/", views.BibleOverviewAPIView.as_view(), name="overview"),
    path("", include(router.urls)),
]
