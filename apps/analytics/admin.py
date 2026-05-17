"""
Django admin configuration for analytics app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.analytics.models import (
    AnalyticsEvent, PropertyAnalytics, UserAnalytics,
    RevenueAnalytics, DashboardMetric, Report
)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    """
    Admin interface for AnalyticsEvent model.
    """
    list_display = [
        'id', 'event_type', 'user', 'content_type', 'object_id',
        'created_at'
    ]
    list_filter = [
        'event_type', 'created_at'
    ]
    search_fields = [
        'user__email', 'event_data'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Event Information'), {
            'fields': ('id', 'event_type', 'user', 'created_at')
        }),
        (_('Related Object'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Event Data'), {
            'fields': ('event_data',),
            'classes': ('collapse',)
        }),
        (_('Context'), {
            'fields': ('url', 'referrer', 'user_agent', 'ip_address', 'session_id'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of analytics events."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow staff to delete old analytics events."""
        if request.user.is_staff:
            return True
        return False


@admin.register(PropertyAnalytics)
class PropertyAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for PropertyAnalytics model.
    """
    list_display = [
        'property', 'total_views', 'inquiries_count', 'bookings_count',
        'trending_score', 'last_viewed'
    ]
    list_filter = ['last_viewed']
    search_fields = ['property__title', 'property__city']
    readonly_fields = [
        'property', 'created_at', 'updated_at'
    ]
    ordering = ['-trending_score']

    fieldsets = (
        (_('Property'), {
            'fields': ('property',)
        }),
        (_('View Metrics'), {
            'fields': ('total_views', 'unique_views', 'view_duration_avg', 'last_viewed')
        }),
        (_('Engagement Metrics'), {
            'fields': ('inquiries_count', 'favorites_count', 'shares_count', 'reviews_count')
        }),
        (_('Booking Metrics'), {
            'fields': ('bookings_count', 'booking_conversion_rate')
        }),
        (_('Performance'), {
            'fields': ('trending_score', 'search_rank_avg', 'click_through_rate')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of property analytics."""
        return False


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for UserAnalytics model.
    """
    list_display = [
        'user', 'total_sessions', 'total_page_views', 'bookings_made',
        'last_activity', 'user_segment'
    ]
    list_filter = ['user_segment', 'last_activity']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'user', 'created_at', 'updated_at'
    ]
    ordering = ['-last_activity']

    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Activity Metrics'), {
            'fields': (
                'total_sessions', 'total_page_views', 'total_search_queries',
                'avg_session_duration', 'bounce_rate'
            )
        }),
        (_('Engagement Metrics'), {
            'fields': (
                'properties_viewed', 'properties_favorited', 'inquiries_sent',
                'bookings_made', 'reviews_written'
            )
        }),
        (_('Status'), {
            'fields': ('last_login', 'last_activity', 'user_segment')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of user analytics."""
        return False


@admin.register(RevenueAnalytics)
class RevenueAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for RevenueAnalytics model.
    """
    list_display = [
        'date', 'period', 'total_revenue', 'booking_revenue',
        'total_bookings', 'new_users'
    ]
    list_filter = ['period', 'date']
    search_fields = ['date']
    readonly_fields = [
        'date', 'period', 'created_at', 'updated_at'
    ]
    ordering = ['-date']

    fieldsets = (
        (_('Time Period'), {
            'fields': ('date', 'period')
        }),
        (_('Revenue Metrics'), {
            'fields': ('total_revenue', 'booking_revenue', 'commission_revenue')
        }),
        (_('Transaction Metrics'), {
            'fields': ('total_bookings', 'successful_payments', 'failed_payments')
        }),
        (_('Property Metrics'), {
            'fields': ('properties_listed', 'properties_rented', 'properties_sold')
        }),
        (_('User Metrics'), {
            'fields': ('new_users', 'active_users')
        }),
        (_('Platform Metrics'), {
            'fields': ('total_views', 'total_searches', 'conversion_rate')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of revenue analytics."""
        return False


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for DashboardMetric model.
    """
    list_display = [
        'metric_type', 'value', 'previous_value', 'change_percentage',
        'last_updated'
    ]
    list_filter = ['metric_type', 'last_updated']
    search_fields = ['metric_type']
    readonly_fields = [
        'metric_type', 'created_at', 'updated_at'
    ]
    ordering = ['metric_type']

    fieldsets = (
        (_('Metric'), {
            'fields': ('metric_type', 'value', 'value_text')
        }),
        (_('Change Tracking'), {
            'fields': ('previous_value', 'change_percentage', 'last_updated')
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of dashboard metrics."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow staff to manage dashboard metrics."""
        return request.user.is_staff


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Admin interface for Report model.
    """
    list_display = [
        'title', 'report_type', 'created_by', 'is_ready',
        'generation_time', 'created_at'
    ]
    list_filter = ['report_type', 'is_ready', 'created_at']
    search_fields = ['title', 'created_by__email']
    readonly_fields = [
        'id', 'created_at', 'file_path', 'file_size',
        'generation_time', 'is_ready'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Report Information'), {
            'fields': ('id', 'title', 'description', 'report_type')
        }),
        (_('Generation'), {
            'fields': ('created_by', 'parameters', 'is_ready', 'generation_time')
        }),
        (_('File'), {
            'fields': ('file_path', 'file_size'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of reports."""
        return False

    actions = ['regenerate_report']

    @admin.action(description=_('Regenerate selected reports'))
    def regenerate_report(self, request, queryset):
        """Regenerate selected reports."""
        from apps.analytics.services.analytics import AnalyticsService

        regenerated = 0
        for report in queryset:
            try:
                new_report = AnalyticsService.generate_report(
                    report.report_type,
                    report.parameters,
                    report.created_by
                )
                regenerated += 1
            except Exception as e:
                self.message_user(
                    request,
                    _(f'Failed to regenerate report "{report.title}": {e}'),
                    level='error'
                )

        self.message_user(
            request,
            ngettext(
                '%d report was successfully regenerated.',
                '%d reports were successfully regenerated.',
                regenerated,
            ) % regenerated,
        )