"""
Search Service for Kirokiro.
"""
import logging

logger = logging.getLogger(__name__)


class PropertySearchService:
    """
    Service for searching properties.
    """
    
    def __init__(self):
        self.logger = logger
    
    def search_properties(self, query_params):
        """
        Search properties based on query parameters with filtering, sorting and pagination support.
        """
        from apps.properties.models import Property
        from django.db.models import Q

        queryset = Property.objects.active().with_related()

        # Text search
        q = query_params.get('q') or query_params.get('query')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q)
            )

        # Apply filters
        if 'city' in query_params:
            queryset = queryset.filter(city__iexact=query_params['city'])
        if 'min_price' in query_params:
            queryset = queryset.filter(rent_price__gte=query_params['min_price'])
        if 'max_price' in query_params:
            queryset = queryset.filter(rent_price__lte=query_params['max_price'])
        if 'bedrooms' in query_params:
            queryset = queryset.filter(bedrooms__gte=query_params['bedrooms'])

        return queryset.distinct()

    def save_search(self, user, name, query_params):
        """
        Save a search for a user.
        """
        from apps.search.models import SavedSearch
        SavedSearch.objects.create(
            user=user,
            name=name,
            search_params=query_params
        )