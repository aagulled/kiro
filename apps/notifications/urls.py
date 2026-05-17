"""
URL configuration for notifications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.views import NotificationViewSet, NotificationPreferenceViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preferences')
router.register(r'', NotificationViewSet, basename='notifications')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]