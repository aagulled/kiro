"""
URL configuration for activity app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.activity.views import ActivityViewSet, AuditViewSet, SecurityEventViewSet

router = DefaultRouter()
router.register(r'logs', ActivityViewSet, basename='activity-logs')
router.register(r'audit', AuditViewSet, basename='audit-logs')
router.register(r'security', SecurityEventViewSet, basename='security-events')

urlpatterns = [
    path('', include(router.urls)),
]