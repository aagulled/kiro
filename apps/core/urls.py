"""
URL configuration for core app.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.HealthCheckView.as_view(), name="health-check"),
]
