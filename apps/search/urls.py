"""
URL configuration for search app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.search.views import SearchViewSet, SavedSearchViewSet

router = DefaultRouter()
router.register(r'saved-searches', SavedSearchViewSet, basename='saved-searches')

urlpatterns = [
    path('', include(router.urls)),
    # Search endpoints
    path('properties/', SearchViewSet.as_view({'get': 'properties'}), name='property-search'),
    path('autocomplete/', SearchViewSet.as_view({'get': 'autocomplete'}), name='search-autocomplete'),
    path('popular-searches/', SearchViewSet.as_view({'get': 'popular_searches'}), name='popular-searches'),
    path('featured-properties/', SearchViewSet.as_view({'get': 'featured_properties'}), name='featured-properties'),
    path('properties/<uuid:pk>/similar/', SearchViewSet.as_view({'get': 'similar_properties'}), name='similar-properties'),
]