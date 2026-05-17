"""
Analytics service for Kirokiro property platform.
Provides reporting, metrics calculation, and dashboard functionality.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.db.models import (
    Count, Sum, Avg, Q, F, Value,
    Case, When, DecimalField, IntegerField
)
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from apps.analytics.models import (
    AnalyticsEvent, PropertyAnalytics, UserAnalytics,
    RevenueAnalytics, DashboardMetric, Report
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for analytics operations and reporting.
    """

    CACHE_TIMEOUT = 3600  # 1 hour

    @staticmethod
    def track_event(
        event_type: str,
        user=None,
        session_id: str = '',
        event_data: Dict[str, Any] = None,
        url: str = '',
        referrer: str = '',
        user_agent: str = '',
        ip_address: str = '',
        content_object=None
    ) -> AnalyticsEvent:
        """
        Track an analytics event.

        Args:
            event_type: Type of event
            user: User performing the action
            session_id: Session identifier
            event_data: Additional event data
            url: Current URL
            referrer: Referrer URL
            user_agent: User agent string
            ip_address: IP address
            content_object: Related model instance

        Returns:
            AnalyticsEvent: Created event instance
        """
        event = AnalyticsEvent.objects.create(
            event_type=event_type,
            user=user,
            session_id=session_id,
            event_data=event_data or {},
            url=url,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        if content_object:
            event.content_type = content_object._meta.label_lower.split('.')
            event.object_id = content_object.pk
            event.save()

        # Update related analytics
        AnalyticsService._update_related_analytics(event)

        return event

    @staticmethod
    def _update_related_analytics(event: AnalyticsEvent):
        """Update related analytics models based on event."""
        try:
            # Update user analytics
            if event.user:
                user_analytics, created = UserAnalytics.objects.get_or_create(
                    user=event.user,
                    defaults={}
                )
                user_analytics.update_activity_metrics(event.event_type)

            # Update property analytics
            if event.content_type and event.content_type.model == 'property':
                from apps.properties.models import Property
                try:
                    property_obj = Property.objects.get(pk=event.object_id)
                    prop_analytics, created = PropertyAnalytics.objects.get_or_create(
                        property=property_obj,
                        defaults={}
                    )

                    if event.event_type == 'property_view':
                        duration = event.event_data.get('duration')
                        prop_analytics.update_view_metrics(duration=duration)
                    elif event.event_type in ['inquiry', 'favorite', 'share', 'review', 'booking']:
                        prop_analytics.update_engagement_metrics(event.event_type)

                except Property.DoesNotExist:
                    pass

        except Exception as e:
            logger.exception(f"Failed to update related analytics: {e}")

    @staticmethod
    def get_dashboard_metrics() -> Dict[str, Any]:
        """
        Get key dashboard metrics.

        Returns:
            Dictionary of dashboard metrics
        """
        cache_key = 'dashboard_metrics'
        cached_metrics = cache.get(cache_key)

        if cached_metrics:
            return cached_metrics

        metrics = {}

        # User metrics
        from django.contrib.auth import get_user_model
        User = get_user_model()

        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()

        metrics['total_users'] = total_users
        metrics['active_users'] = active_users

        # Property metrics
        from apps.properties.models import Property, PropertyStatus

        total_properties = Property.objects.filter(is_deleted=False).count()
        active_properties = Property.objects.filter(
            status=PropertyStatus.ACTIVE,
            is_deleted=False
        ).count()

        metrics['total_properties'] = total_properties
        metrics['active_properties'] = active_properties

        # Booking metrics
        from apps.bookings.models import Booking

        total_bookings = Booking.objects.count()
        recent_bookings = Booking.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        metrics['total_bookings'] = total_bookings
        metrics['recent_bookings'] = recent_bookings

        # Revenue metrics
        from apps.bookings.models import Payment

        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_revenue = Payment.objects.filter(
            status='completed',
            created_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0

        metrics['total_revenue'] = float(total_revenue)
        metrics['monthly_revenue'] = float(monthly_revenue)

        # Activity metrics
        total_views = AnalyticsEvent.objects.filter(
            event_type='property_view'
        ).count()

        total_searches = AnalyticsEvent.objects.filter(
            event_type='search'
        ).count()

        metrics['total_views'] = total_views
        metrics['total_searches'] = total_searches

        # Conversion rate
        if total_views > 0:
            bookings_from_views = AnalyticsEvent.objects.filter(
                event_type='booking',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            conversion_rate = (bookings_from_views / total_views) * 100
        else:
            conversion_rate = 0

        metrics['conversion_rate'] = round(conversion_rate, 2)

        # Update cached dashboard metrics
        for metric_type, value in metrics.items():
            metric, created = DashboardMetric.objects.get_or_create(
                metric_type=metric_type,
                defaults={'value': value}
            )
            if not created:
                metric.update_value(value)

        cache.set(cache_key, metrics, AnalyticsService.CACHE_TIMEOUT)

        return metrics

    @staticmethod
    def get_revenue_report(
        start_date: datetime,
        end_date: datetime,
        group_by: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Generate revenue report for a date range.

        Args:
            start_date: Start date for report
            end_date: End date for report
            group_by: Grouping ('daily', 'weekly', 'monthly')

        Returns:
            List of revenue data points
        """
        from apps.bookings.models import Payment, Booking
        from apps.properties.models import Property

        # Determine truncate function
        if group_by == 'weekly':
            trunc_func = TruncWeek
        elif group_by == 'monthly':
            trunc_func = TruncMonth
        else:
            trunc_func = TruncDate

        # Revenue data
        revenue_data = Payment.objects.filter(
            status='completed',
            created_at__range=(start_date, end_date)
        ).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            revenue=Sum('amount'),
            commission=Sum('commission_amount'),
            payments_count=Count('id')
        ).order_by('period')

        # Booking data
        booking_data = Booking.objects.filter(
            created_at__range=(start_date, end_date)
        ).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            bookings_count=Count('id')
        ).order_by('period')

        # Property data
        property_data = Property.objects.filter(
            created_at__range=(start_date, end_date)
        ).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            properties_listed=Count('id')
        ).order_by('period')

        # User data
        user_data = AnalyticsEvent.objects.filter(
            event_type='signup',
            created_at__range=(start_date, end_date)
        ).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            new_users=Count('id')
        ).order_by('period')

        # Combine data
        report_data = {}
        periods = set()

        # Collect all periods
        for data in [revenue_data, booking_data, property_data, user_data]:
            periods.update(item['period'] for item in data)

        # Build report
        for period in sorted(periods):
            period_str = period.strftime('%Y-%m-%d')

            revenue_info = next((r for r in revenue_data if r['period'] == period), {})
            booking_info = next((b for b in booking_data if b['period'] == period), {})
            property_info = next((p for p in property_data if p['period'] == period), {})
            user_info = next((u for u in user_data if u['period'] == period), {})

            report_data[period_str] = {
                'period': period_str,
                'revenue': float(revenue_info.get('revenue', 0)),
                'commission': float(revenue_info.get('commission', 0)),
                'payments_count': revenue_info.get('payments_count', 0),
                'bookings_count': booking_info.get('bookings_count', 0),
                'properties_listed': property_info.get('properties_listed', 0),
                'new_users': user_info.get('new_users', 0),
            }

        return list(report_data.values())

    @staticmethod
    def get_property_performance_report(
        property_ids: List[int] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Generate property performance report.

        Args:
            property_ids: List of property IDs to include
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            List of property performance data
        """
        from apps.properties.models import Property

        queryset = Property.objects.filter(is_deleted=False)

        if property_ids:
            queryset = queryset.filter(id__in=property_ids)

        if start_date and end_date:
            queryset = queryset.filter(created_at__range=(start_date, end_date))

        # Get analytics data
        properties_data = []
        for property_obj in queryset:
            analytics = getattr(property_obj, 'analytics', None)
            if not analytics:
                continue

            # Get recent events
            recent_events = AnalyticsEvent.objects.filter(
                content_type__model='property',
                object_id=property_obj.id,
                created_at__gte=timezone.now() - timedelta(days=30)
            )

            views_30d = recent_events.filter(event_type='property_view').count()
            inquiries_30d = recent_events.filter(event_type='inquiry').count()
            bookings_30d = recent_events.filter(event_type='booking').count()

            properties_data.append({
                'property_id': property_obj.id,
                'title': property_obj.title,
                'owner': property_obj.owner.email if property_obj.owner else '',
                'status': property_obj.status,
                'total_views': analytics.total_views,
                'views_30d': views_30d,
                'inquiries_count': analytics.inquiries_count,
                'inquiries_30d': inquiries_30d,
                'bookings_count': analytics.bookings_count,
                'bookings_30d': bookings_30d,
                'favorites_count': analytics.favorites_count,
                'reviews_count': analytics.reviews_count,
                'trending_score': float(analytics.trending_score),
            })

        return sorted(properties_data, key=lambda x: x['trending_score'], reverse=True)

    @staticmethod
    def get_user_activity_report(
        start_date: datetime = None,
        end_date: datetime = None,
        user_segment: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate user activity report.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            user_segment: User segment to filter by

        Returns:
            List of user activity data
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        queryset = User.objects.all()

        if user_segment:
            queryset = queryset.filter(
                analytics__user_segment=user_segment
            )

        users_data = []
        for user in queryset:
            analytics = getattr(user, 'analytics', None)
            if not analytics:
                continue

            # Get activity in date range
            activity_filter = Q()
            if start_date and end_date:
                activity_filter = Q(created_at__range=(start_date, end_date))

            events = AnalyticsEvent.objects.filter(
                user=user
            ).filter(activity_filter)

            recent_activity = events.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()

            users_data.append({
                'user_id': user.id,
                'email': user.email,
                'name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'date_joined': user.created_at,
                'last_login': user.last_login,
                'total_sessions': analytics.total_sessions,
                'total_page_views': analytics.total_page_views,
                'properties_viewed': analytics.properties_viewed,
                'inquiries_sent': analytics.inquiries_sent,
                'bookings_made': analytics.bookings_made,
                'reviews_written': analytics.reviews_written,
                'recent_activity': recent_activity,
                'user_segment': analytics.user_segment,
            })

        return users_data

    @staticmethod
    def generate_report(
        report_type: str,
        parameters: Dict[str, Any],
        user=None
    ) -> Report:
        """
        Generate and save a report.

        Args:
            report_type: Type of report to generate
            parameters: Report parameters
            user: User generating the report

        Returns:
            Report: Generated report instance
        """
        import csv
        import io
        from django.core.files.base import ContentFile

        report = Report.objects.create(
            report_type=report_type,
            title=f"{report_type.replace('_', ' ').title()} Report",
            parameters=parameters,
            created_by=user,
        )

        try:
            start_time = timezone.now()

            # Generate report data based on type
            if report_type == 'revenue':
                data = AnalyticsService.get_revenue_report(
                    parameters.get('start_date'),
                    parameters.get('end_date'),
                    parameters.get('group_by', 'daily')
                )
                headers = ['Period', 'Revenue', 'Commission', 'Payments', 'Bookings', 'Properties Listed', 'New Users']

            elif report_type == 'property_performance':
                data = AnalyticsService.get_property_performance_report(
                    parameters.get('property_ids'),
                    parameters.get('start_date'),
                    parameters.get('end_date')
                )
                headers = ['Property ID', 'Title', 'Owner', 'Status', 'Total Views', 'Views (30d)',
                          'Inquiries', 'Inquiries (30d)', 'Bookings', 'Bookings (30d)',
                          'Favorites', 'Reviews', 'Trending Score']

            elif report_type == 'user_activity':
                data = AnalyticsService.get_user_activity_report(
                    parameters.get('start_date'),
                    parameters.get('end_date'),
                    parameters.get('user_segment')
                )
                headers = ['User ID', 'Email', 'Name', 'Role', 'Active', 'Date Joined',
                          'Last Login', 'Sessions', 'Page Views', 'Properties Viewed',
                          'Inquiries', 'Bookings', 'Reviews', 'Recent Activity', 'Segment']

            # Create CSV file
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)

            for row in data:
                writer.writerow([row.get(header.lower().replace(' ', '_'), '') for header in headers])

            # Save file
            content = ContentFile(output.getvalue().encode('utf-8'))
            report.file_path.save(f"{report_type}_{report.id}.csv", content)
            report.file_size = content.size

            # Update generation time
            generation_time = (timezone.now() - start_time).total_seconds()
            report.generation_time = generation_time
            report.is_ready = True
            report.save()

            logger.info(f"Generated {report_type} report {report.id} in {generation_time}s")

        except Exception as e:
            logger.exception(f"Failed to generate {report_type} report: {e}")
            report.delete()
            raise

        return report

    @staticmethod
    def get_popular_properties(limit: int = 10, timeframe_days: int = 30) -> List[Dict[str, Any]]:
        """
        Get most popular properties based on recent activity.

        Args:
            limit: Number of properties to return
            timeframe_days: Number of days to look back

        Returns:
            List of popular properties with metrics
        """
        from apps.properties.models import Property

        # Get properties with recent activity
        recent_events = AnalyticsEvent.objects.filter(
            content_type__model='property',
            event_type__in=['property_view', 'inquiry', 'booking', 'favorite'],
            created_at__gte=timezone.now() - timedelta(days=timeframe_days)
        ).values('object_id').annotate(
            activity_score=Count('id')
        ).order_by('-activity_score')[:limit*2]

        property_ids = [event['object_id'] for event in recent_events]
        properties = Property.objects.filter(
            id__in=property_ids,
            status='active',
            is_deleted=False
        ).select_related('owner')

        popular_properties = []
        for property_obj in properties:
            analytics = getattr(property_obj, 'analytics', None)
            if analytics:
                # Calculate recent activity
                recent_views = AnalyticsEvent.objects.filter(
                    content_type__model='property',
                    object_id=property_obj.id,
                    event_type='property_view',
                    created_at__gte=timezone.now() - timedelta(days=timeframe_days)
                ).count()

                popular_properties.append({
                    'property': property_obj,
                    'total_views': analytics.total_views,
                    'recent_views': recent_views,
                    'inquiries_count': analytics.inquiries_count,
                    'bookings_count': analytics.bookings_count,
                    'trending_score': float(analytics.trending_score),
                })

        return sorted(popular_properties, key=lambda x: x['trending_score'], reverse=True)[:limit]