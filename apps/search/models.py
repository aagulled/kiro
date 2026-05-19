"""
Search models for Kirokiro property platform.
"""
import uuid
from django.contrib.postgres.search import SearchVectorField, SearchHeadline
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import TimestampMixin


class SavedSearch(TimestampMixin, models.Model):
    """
    User-persisted search query with alert frequency settings.
    """

    FREQUENCY_CHOICES = [
        ('never', _('Never')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_searches'
    )
    name = models.CharField(max_length=255)
    search_params = models.JSONField(help_text="Saved search parameters")

    # Notification settings
    email_notifications = models.BooleanField(default=False)
    notification_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='never'
    )

    # Search metadata
    last_run_at = models.DateTimeField(null=True, blank=True)
    result_count = models.PositiveIntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Saved Search")
        verbose_name_plural = _("Saved Searches")
        ordering = ['-updated_at']
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_run_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class SearchQuery(TimestampMixin, models.Model):
    """
    Logged user search query with filters and result count for analytics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries'
    )
    session_id = models.CharField(max_length=255, blank=True)

    # Search parameters
    query = models.CharField(max_length=500, blank=True)
    filters = models.JSONField(default=dict)
    sort_by = models.CharField(max_length=100, blank=True)
    page = models.PositiveIntegerField(default=1)

    # Results
    result_count = models.PositiveIntegerField(default=0)
    execution_time = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Search execution time in seconds"
    )

    # Metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True, help_text="Search source (web, mobile, api)")

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return f"Search: {self.query or 'No query'} - {self.result_count} results"


class PopularSearch(TimestampMixin, models.Model):
    """
    Aggregated popular search term with count and last-seen timestamp.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    term = models.CharField(max_length=255, unique=True)
    search_count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(auto_now=True)

    # Popularity metrics
    trending_score = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Popular Search")
        verbose_name_plural = _("Popular Searches")
        ordering = ['-search_count', '-trending_score']
        indexes = [
            models.Index(fields=['term']),
            models.Index(fields=['search_count']),
            models.Index(fields=['trending_score']),
        ]

    def __str__(self):
        return f"{self.term} ({self.search_count} searches)"

    def increment_count(self):
        """Increment search count and update trending score."""
        from django.utils import timezone
        from datetime import timedelta

        self.search_count += 1

        # Calculate trending score based on recent activity
        recent_searches = PopularSearch.objects.filter(
            term=self.term,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        # Simple trending algorithm: combine total count with recent activity
        self.trending_score = self.search_count * 0.7 + recent_searches * 0.3

        self.save(update_fields=['search_count', 'trending_score'])


class PropertySearchIndex(TimestampMixin, models.Model):
    """
    Search index for properties to enable fast full-text search.
    """

    property = models.OneToOneField(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='search_index'
    )

    # Full-text search fields
    search_vector = SearchVectorField(null=True, blank=True)

    # Indexed fields for filtering
    title_vector = models.TextField(blank=True)
    description_vector = models.TextField(blank=True)
    location_vector = models.TextField(blank=True)
    amenities_vector = models.TextField(blank=True)

    # Pre-computed filter values
    price_range = models.CharField(max_length=50, blank=True)
    bedroom_range = models.CharField(max_length=50, blank=True)
    property_type = models.CharField(max_length=50, blank=True)

    # Search metadata
    last_indexed = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Property Search Index")
        verbose_name_plural = _("Property Search Indexes")
        indexes = [
            models.Index(fields=['search_vector']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price_range']),
            models.Index(fields=['bedroom_range']),
            models.Index(fields=['property_type']),
        ]

    def __str__(self):
        return f"Search index for {self.property.title}"

    def update_index(self):
        """Update the search index for this property."""
        from django.contrib.postgres.search import SearchVector
        from apps.properties.models import Amenity

        # Combine searchable text
        title = self.property.title or ''
        description = self.property.description or ''
        address = f"{self.property.city} {self.property.state} {self.property.country}"
        amenities = ' '.join(
            self.property.amenities.values_list('name', flat=True)
        ) if self.property.amenities.exists() else ''

        # Create search vectors
        self.title_vector = title
        self.description_vector = description
        self.location_vector = address
        self.amenities_vector = amenities

        # Create combined search vector
        self.search_vector = (
            SearchVector('title_vector', weight='A') +
            SearchVector('description_vector', weight='B') +
            SearchVector('location_vector', weight='C') +
            SearchVector('amenities_vector', weight='D')
        )

        # Set filter values
        self.property_type = self.property.category

        if self.property.rent_price:
            if self.property.rent_price < 500:
                self.price_range = '0-500'
            elif self.property.rent_price < 1000:
                self.price_range = '500-1000'
            elif self.property.rent_price < 2000:
                self.price_range = '1000-2000'
            else:
                self.price_range = '2000+'
        elif self.property.sale_price:
            if self.property.sale_price < 50000:
                self.price_range = '0-50000'
            elif self.property.sale_price < 100000:
                self.price_range = '50000-100000'
            elif self.property.sale_price < 200000:
                self.price_range = '100000-200000'
            else:
                self.price_range = '200000+'

        if self.property.bedrooms == 0:
            self.bedroom_range = 'studio'
        elif self.property.bedrooms == 1:
            self.bedroom_range = '1'
        elif self.property.bedrooms <= 3:
            self.bedroom_range = '2-3'
        else:
            self.bedroom_range = '4+'

        self.save()


class SearchSuggestion(TimestampMixin, models.Model):
    """
    Autocomplete suggestions for search.
    """

    term = models.CharField(max_length=255, unique=True)
    frequency = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Search Suggestion")
        verbose_name_plural = _("Search Suggestions")
        ordering = ['-frequency', 'term']

    def __str__(self):
        return f"{self.term} ({self.frequency})"