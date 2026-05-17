"""
URL configuration for analytics app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.analytics.views import AnalyticsViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
    # Analytics endpoints
    path('dashboard/', AnalyticsViewSet.as_view({'get': 'dashboard'}), name='analytics-dashboard'),
    path('revenue-report/', AnalyticsViewSet.as_view({'get': 'revenue_report'}), name='revenue-report'),
    path('property-performance/', AnalyticsViewSet.as_view({'get': 'property_performance'}), name='property-performance'),
    path('user-activity/', AnalyticsViewSet.as_view({'get': 'user_activity'}), name='user-activity'),
    path('popular-properties/', AnalyticsViewSet.as_view({'get': 'popular_properties'}), name='popular-properties'),
    path('track-event/', AnalyticsViewSet.as_view({'post': 'track_event'}), name='track-event'),
]