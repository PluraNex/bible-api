"""
URL configuration for Bible auth app.
"""
from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    path("status/", views.AuthStatusAPIView.as_view(), name="status"),
    path("register/", views.DeveloperRegistrationAPIView.as_view(), name="developer_register"),
]
