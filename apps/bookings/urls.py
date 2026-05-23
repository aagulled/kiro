"""
URLs for the bookings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .viewsets import BookingViewSet

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
]
