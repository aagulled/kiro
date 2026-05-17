"""
Analytics models for Kirokiro property platform.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import TimestampMixin


class AnalyticsEvent(TimestampMixin, models.Model):
    """
    Generic analytics event model for tracking user actions and system events.
    """

    EVENT_TYPES = [
        ('page_view', _('Page View')),
        ('property_view', _('Property View')),
        ('search', _('Search')),
        ('inquiry', _('Inquiry')),
        ('booking', _('Booking')),
        ('payment', _('Payment')),
        ('review', _('Review')),
        ('favorite', _('Favorite')),
        ('share', _('Share')),
        ('contact', _('Contact')),
        ('signup', _('Sign Up')),
        ('login', _('Login')),
        ('logout', _('Logout')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events'
    )
    session_id = models.CharField(max_length=255, blank=True)

    # Event data
    event_data = models.JSONField(default=dict, help_text="Additional event data")

    # Context
    url = models.URLField(blank=True)
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Related objects (generic relations)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Analytics Event")
        verbose_name_plural = _("Analytics Events")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user or 'Anonymous'}"


class PropertyAnalytics(TimestampMixin, models.Model):
    """
    Analytics data for properties.
    """

    property = models.OneToOneField(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # View metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    view_duration_avg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Average view duration in seconds"
    )

    # Engagement metrics
    inquiries_count = models.PositiveIntegerField(default=0)
    favorites_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)

    # Booking metrics
    bookings_count = models.PositiveIntegerField(default=0)
    booking_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of views that convert to bookings"
    )

    # Time-based metrics
    last_viewed = models.DateTimeField(null=True, blank=True)
    trending_score = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
        help_text="Trending score based on recent activity"
    )

    # Performance metrics
    search_rank_avg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Average search ranking"
    )
    click_through_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="CTR from search results"
    )

    class Meta:
        verbose_name = _("Property Analytics")
        verbose_name_plural = _("Property Analytics")

    def __str__(self):
        return f"Analytics for {self.property.title}"

    def update_view_metrics(self, duration=None, unique=True):
        """Update view-related metrics."""
        self.total_views += 1
        if unique:
            self.unique_views += 1
        if duration:
            # Calculate running average
            total_duration = self.view_duration_avg * (self.total_views - 1) + duration
            self.view_duration_avg = total_duration / self.total_views
        self.last_viewed = self.updated_at
        self.save()

    def update_engagement_metrics(self, metric_type, increment=1):
        """Update engagement metrics."""
        if metric_type == 'inquiry':
            self.inquiries_count += increment
        elif metric_type == 'favorite':
            self.favorites_count += increment
        elif metric_type == 'share':
            self.shares_count += increment
        elif metric_type == 'review':
            self.reviews_count += increment
        elif metric_type == 'booking':
            self.bookings_count += increment
            # Recalculate conversion rate
            if self.total_views > 0:
                self.booking_conversion_rate = (self.bookings_count / self.total_views) * 100

        self.save()

    def calculate_trending_score(self):
        """Calculate trending score based on recent activity."""
        from datetime import timedelta
        from django.utils import timezone

        # Get recent activity (last 7 days)
        recent_events = AnalyticsEvent.objects.filter(
            content_type__model='property',
            object_id=self.property.id,
            created_at__gte=timezone.now() - timedelta(days=7)
        )

        # Simple trending algorithm
        recent_views = recent_events.filter(event_type='property_view').count()
        recent_inquiries = recent_events.filter(event_type='inquiry').count()
        recent_bookings = recent_events.filter(event_type='booking').count()

        # Weight recent activity
        self.trending_score = (
            recent_views * 0.3 +
            recent_inquiries * 0.5 +
            recent_bookings * 0.2
        )

        self.save()


class UserAnalytics(TimestampMixin, models.Model):
    """
    Analytics data for users.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Activity metrics
    total_sessions = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    total_search_queries = models.PositiveIntegerField(default=0)

    # Property-related metrics
    properties_viewed = models.PositiveIntegerField(default=0)
    properties_favorited = models.PositiveIntegerField(default=0)
    inquiries_sent = models.PositiveIntegerField(default=0)
    bookings_made = models.PositiveIntegerField(default=0)
    reviews_written = models.PositiveIntegerField(default=0)

    # Engagement metrics
    avg_session_duration = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Average session duration in minutes"
    )
    bounce_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of single-page sessions"
    )

    # Last activity
    last_login = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    # User segment
    user_segment = models.CharField(
        max_length=50,
        blank=True,
        help_text="User segmentation (e.g., 'active', 'casual', 'inactive')"
    )

    class Meta:
        verbose_name = _("User Analytics")
        verbose_name_plural = _("User Analytics")

    def __str__(self):
        return f"Analytics for {self.user.email}"

    def update_activity_metrics(self, event_type, session_duration=None):
        """Update user activity metrics."""
        if event_type == 'login':
            self.last_login = self.updated_at
        elif event_type == 'page_view':
            self.total_page_views += 1
        elif event_type == 'search':
            self.total_search_queries += 1
        elif event_type == 'property_view':
            self.properties_viewed += 1
        elif event_type == 'favorite':
            self.properties_favorited += 1
        elif event_type == 'inquiry':
            self.inquiries_sent += 1
        elif event_type == 'booking':
            self.bookings_made += 1
        elif event_type == 'review':
            self.reviews_written += 1

        self.last_activity = self.updated_at

        if session_duration:
            # Update average session duration
            total_sessions_duration = self.avg_session_duration * self.total_sessions + session_duration
            self.total_sessions += 1
            self.avg_session_duration = total_sessions_duration / self.total_sessions

        self.save()

    def update_user_segment(self):
        """Update user segment based on activity."""
        from datetime import timedelta
        from django.utils import timezone

        # Define segments based on activity
        recent_activity = AnalyticsEvent.objects.filter(
            user=self.user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        if recent_activity >= 50:
            self.user_segment = 'highly_active'
        elif recent_activity >= 20:
            self.user_segment = 'active'
        elif recent_activity >= 5:
            self.user_segment = 'casual'
        else:
            self.user_segment = 'inactive'

        self.save()


class RevenueAnalytics(TimestampMixin, models.Model):
    """
    Revenue and financial analytics.
    """

    # Time period
    date = models.DateField(unique=True)
    period = models.CharField(max_length=20, default='daily')  # daily, weekly, monthly

    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    booking_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Transaction metrics
    total_bookings = models.PositiveIntegerField(default=0)
    successful_payments = models.PositiveIntegerField(default=0)
    failed_payments = models.PositiveIntegerField(default=0)

    # Property metrics
    properties_listed = models.PositiveIntegerField(default=0)
    properties_rented = models.PositiveIntegerField(default=0)
    properties_sold = models.PositiveIntegerField(default=0)

    # User metrics
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)

    # Platform metrics
    total_views = models.PositiveIntegerField(default=0)
    total_searches = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Revenue Analytics")
        verbose_name_plural = _("Revenue Analytics")
        ordering = ['-date']
        unique_together = ['date', 'period']
        indexes = [
            models.Index(fields=['date', 'period']),
        ]

    def __str__(self):
        return f"Analytics for {self.date} ({self.period})"


class DashboardMetric(TimestampMixin, models.Model):
    """
    Cached dashboard metrics for quick access.
    """

    METRIC_TYPES = [
        ('total_users', _('Total Users')),
        ('active_users', _('Active Users')),
        ('total_properties', _('Total Properties')),
        ('active_properties', _('Active Properties')),
        ('total_bookings', _('Total Bookings')),
        ('monthly_revenue', _('Monthly Revenue')),
        ('total_views', _('Total Views')),
        ('conversion_rate', _('Conversion Rate')),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, unique=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    value_text = models.CharField(max_length=255, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Change tracking
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _("Dashboard Metric")
        verbose_name_plural = _("Dashboard Metrics")

    def __str__(self):
        return f"{self.metric_type}: {self.value}"

    def update_value(self, new_value, new_value_text=''):
        """Update metric value and calculate change."""
        if self.value != 0:
            self.change_percentage = ((new_value - self.value) / self.value) * 100
        else:
            self.change_percentage = 0

        self.previous_value = self.value
        self.value = new_value
        self.value_text = new_value_text
        self.save()


class Report(models.Model):
    """
    Generated reports for download.
    """

    REPORT_TYPES = [
        ('user_activity', _('User Activity Report')),
        ('property_performance', _('Property Performance Report')),
        ('revenue', _('Revenue Report')),
        ('booking', _('Booking Report')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Report parameters
    parameters = models.JSONField(default=dict)

    # Generation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to='reports/', blank=True)
    file_size = models.PositiveIntegerField(default=0)

    # Status
    is_ready = models.BooleanField(default=False)
    generation_time = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Generation time in seconds"
    )

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.report_type})"