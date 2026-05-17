"""
Search API views and serializers.
"""
from rest_framework import viewsets, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.search.services.search import PropertySearchService
from apps.search.models import SavedSearch


class SearchSerializer(serializers.Serializer):
    """Serializer for search parameters."""
    query = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    listing_type = serializers.ChoiceField(
        choices=['rent', 'sale'],
        required=False,
        allow_blank=True
    )
    min_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    min_bedrooms = serializers.IntegerField(required=False, min_value=0)
    max_bedrooms = serializers.IntegerField(required=False, min_value=0)
    min_bathrooms = serializers.IntegerField(required=False, min_value=0)
    amenities = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    furnished = serializers.BooleanField(required=False)
    pets_allowed = serializers.BooleanField(required=False)
    available_from = serializers.DateField(required=False)
    sort_by = serializers.ChoiceField(
        choices=['relevance', 'price_low', 'price_high', 'newest', 'oldest', 'rating', 'popularity'],
        required=False,
        default='relevance'
    )


class SearchViewSet(viewsets.ViewSet):
    """
    ViewSet for property search functionality.
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def properties(self, request):
        """Search properties with advanced filtering."""
        serializer = SearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Extract search parameters
        search_params = serializer.validated_data
        query = search_params.pop('query', '')
        sort_by = search_params.pop('sort_by', 'relevance')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 50)

        # Perform search
        results = PropertySearchService.search_properties(
            query=query,
            filters=search_params,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
            source='api'
        )

        # Serialize results
        from apps.properties.serializers import PropertyListSerializer
        property_serializer = PropertyListSerializer(
            results['results'],
            many=True,
            context={'request': request}
        )

        response_data = {
            'results': property_serializer.data,
            'pagination': {
                'page': results['page'],
                'page_size': results['page_size'],
                'total_count': results['total_count'],
                'total_pages': results['total_pages'],
            },
            'facets': results['facets'],
            'suggestions': results['suggestions'],
            'execution_time': results['execution_time'],
        }

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """Get autocomplete suggestions for search queries."""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'suggestions': []})

        suggestions = PropertySearchService.autocomplete_search(query)
        return Response({'suggestions': suggestions})

    @action(detail=False, methods=['get'])
    def popular_searches(self, request):
        """Get popular search terms."""
        limit = min(int(request.query_params.get('limit', 10)), 50)
        searches = PropertySearchService.get_popular_searches(limit)
        return Response({'popular_searches': searches})

    @action(detail=False, methods=['get'])
    def featured_properties(self, request):
        """Get featured properties."""
        limit = min(int(request.query_params.get('limit', 10)), 50)
        properties = PropertySearchService.get_featured_properties(limit)

        from apps.properties.serializers import PropertyListSerializer
        serializer = PropertyListSerializer(
            properties,
            many=True,
            context={'request': request}
        )

        return Response({'featured_properties': serializer.data})

    @action(detail=True, methods=['get'])
    def similar_properties(self, request, pk=None):
        """Get similar properties for a given property."""
        limit = min(int(request.query_params.get('limit', 5)), 20)
        similar = PropertySearchService.get_similar_properties(pk, limit)

        from apps.properties.serializers import PropertyListSerializer
        serializer = PropertyListSerializer(
            similar,
            many=True,
            context={'request': request}
        )

        return Response({'similar_properties': serializer.data})


class SavedSearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches."""

    class Meta:
        model = SavedSearch
        fields = [
            'id', 'name', 'search_params', 'email_notifications',
            'notification_frequency', 'last_run_at', 'result_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run_at', 'result_count', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate unique name per user."""
        user = self.context['request'].user
        queryset = SavedSearch.objects.filter(user=user, name=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(_("A saved search with this name already exists."))
        return value


class SavedSearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved searches.
    """
    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'email_notifications']

    def get_queryset(self):
        """Return saved searches for the current user."""
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create saved search for current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def run_search(self, request, pk=None):
        """Run a saved search and return results."""
        saved_search = self.get_object()

        # Extract search parameters
        search_params = saved_search.search_params
        query = search_params.get('query', '')
        filters = {k: v for k, v in search_params.items() if k != 'query'}
        sort_by = search_params.get('sort_by', 'relevance')

        # Run search
        results = PropertySearchService.search_properties(
            query=query,
            filters=filters,
            sort_by=sort_by,
            user=request.user,
            source='saved_search'
        )

        # Update saved search metadata
        saved_search.last_run_at = timezone.now()
        saved_search.result_count = results['total_count']
        saved_search.save()

        # Serialize results
        from apps.properties.serializers import PropertyListSerializer
        property_serializer = PropertyListSerializer(
            results['results'][:20],  # Limit to first 20 results
            many=True,
            context={'request': request}
        )

        return Response({
            'saved_search': self.get_serializer(saved_search).data,
            'results': property_serializer.data,
            'total_count': results['total_count'],
        })

    @action(detail=False, methods=['post'])
    def create_from_current_search(self, request):
        """Create a saved search from current search parameters."""
        search_serializer = SearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)

        name = request.data.get('name')
        if not name:
            return Response(
                {'error': _('Name is required for saved search.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if name already exists
        if SavedSearch.objects.filter(user=request.user, name=name).exists():
            return Response(
                {'error': _('A saved search with this name already exists.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_search = SavedSearch.objects.create(
            user=request.user,
            name=name,
            search_params=search_serializer.validated_data
        )

        serializer = self.get_serializer(saved_search)
        return Response(serializer.data, status=status.HTTP_201_CREATED)