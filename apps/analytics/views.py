"""
Analytics API views and serializers.
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

from apps.analytics.models import AnalyticsEvent, PropertyAnalytics, UserAnalytics, Report
from apps.analytics.services.analytics import AnalyticsService


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """Serializer for analytics events."""

    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'event_type', 'user', 'session_id', 'event_data',
            'url', 'referrer', 'user_agent', 'ip_address',
            'content_type', 'object_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PropertyAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for property analytics."""

    property_title = serializers.CharField(source='property.title', read_only=True)
    property_owner = serializers.CharField(source='property.owner.email', read_only=True)

    class Meta:
        model = PropertyAnalytics
        fields = [
            'property', 'property_title', 'property_owner',
            'total_views', 'unique_views', 'view_duration_avg',
            'inquiries_count', 'favorites_count', 'shares_count', 'reviews_count',
            'bookings_count', 'booking_conversion_rate',
            'last_viewed', 'trending_score', 'search_rank_avg', 'click_through_rate'
        ]


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for user analytics."""

    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = UserAnalytics
        fields = [
            'user', 'user_email', 'user_name',
            'total_sessions', 'total_page_views', 'total_search_queries',
            'properties_viewed', 'properties_favorited', 'inquiries_sent',
            'bookings_made', 'reviews_written', 'avg_session_duration',
            'bounce_rate', 'last_login', 'last_activity', 'user_segment'
        ]


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard metrics."""

    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_properties = serializers.IntegerField()
    active_properties = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    recent_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_views = serializers.IntegerField()
    total_searches = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports."""

    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'title', 'description', 'parameters',
            'created_by', 'created_at', 'file_path', 'file_size',
            'is_ready', 'generation_time'
        ]
        read_only_fields = ['id', 'created_at', 'file_path', 'file_size', 'is_ready', 'generation_time']


class ReportGenerationSerializer(serializers.Serializer):
    """Serializer for report generation parameters."""

    report_type = serializers.ChoiceField(
        choices=[
            ('user_activity', _('User Activity Report')),
            ('property_performance', _('Property Performance Report')),
            ('revenue', _('Revenue Report')),
            ('booking', _('Booking Report')),
        ]
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    group_by = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly'],
        required=False,
        default='daily'
    )
    property_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    user_segment = serializers.CharField(required=False, allow_blank=True)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics operations.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics."""
        metrics = AnalyticsService.get_dashboard_metrics()
        serializer = DashboardSerializer(metrics)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def revenue_report(self, request):
        """Get revenue report data."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'daily')

        if not start_date or not end_date:
            return Response(
                {'error': _('start_date and end_date are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
        except ValueError:
            return Response(
                {'error': _('Invalid date format. Use ISO format (YYYY-MM-DD)')},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = AnalyticsService.get_revenue_report(start, end, group_by)
        return Response({'data': data})

    @action(detail=False, methods=['get'])
    def property_performance(self, request):
        """Get property performance report."""
        property_ids = request.query_params.getlist('property_ids', [])
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        params = {}
        if property_ids:
            params['property_ids'] = [int(pid) for pid in property_ids if pid.isdigit()]
        if start_date:
            params['start_date'] = datetime.fromisoformat(start_date)
        if end_date:
            params['end_date'] = datetime.fromisoformat(end_date)

        data = AnalyticsService.get_property_performance_report(**params)
        return Response({'data': data})

    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get user activity report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_segment = request.query_params.get('user_segment')

        params = {}
        if start_date:
            params['start_date'] = datetime.fromisoformat(start_date)
        if end_date:
            params['end_date'] = datetime.fromisoformat(end_date)
        if user_segment:
            params['user_segment'] = user_segment

        data = AnalyticsService.get_user_activity_report(**params)
        return Response({'data': data})

    @action(detail=False, methods=['get'])
    def popular_properties(self, request):
        """Get popular properties."""
        limit = min(int(request.query_params.get('limit', 10)), 50)
        timeframe_days = min(int(request.query_params.get('timeframe_days', 30)), 365)

        properties = AnalyticsService.get_popular_properties(limit, timeframe_days)

        # Serialize the data
        data = []
        for item in properties:
            data.append({
                'property_id': item['property'].id,
                'title': item['property'].title,
                'owner': item['property'].owner.email if item['property'].owner else '',
                'total_views': item['total_views'],
                'recent_views': item['recent_views'],
                'inquiries_count': item['inquiries_count'],
                'bookings_count': item['bookings_count'],
                'trending_score': item['trending_score'],
            })

        return Response({'popular_properties': data})

    @action(detail=False, methods=['post'])
    def track_event(self, request):
        """Track an analytics event."""
        serializer = AnalyticsEventSerializer(data=request.data)
        if serializer.is_valid():
            event_data = serializer.validated_data.copy()
            user = request.user if request.user.is_authenticated else None

            # Track the event
            AnalyticsService.track_event(
                event_type=event_data['event_type'],
                user=user,
                session_id=request.session.session_key or '',
                event_data=event_data.get('event_data', {}),
                url=event_data.get('url', ''),
                referrer=event_data.get('referrer', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )

            return Response({'status': 'event tracked'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for report management.
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report_type', 'is_ready']

    def get_queryset(self):
        """Return reports for the current user or all if staff."""
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """Create report for current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new report."""
        serializer = ReportGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = AnalyticsService.generate_report(
                report_type=serializer.validated_data['report_type'],
                parameters=serializer.validated_data,
                user=request.user
            )

            response_serializer = ReportSerializer(report)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )