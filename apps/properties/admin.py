"""
Django admin configuration for properties app.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext

from apps.properties.models import (
    Property, PropertyImage, PropertyDocument, Amenity,
    Favorite, Inquiry, Review
)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """
    Admin interface for Amenity model.
    """
    list_display = ['name', 'icon', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

    fieldsets = (
        (_('Amenity Information'), {
            'fields': ('name', 'icon', 'description', 'category')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class PropertyImageInline(admin.TabularInline):
    """
    Inline admin for PropertyImage.
    """
    model = PropertyImage
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


class PropertyDocumentInline(admin.TabularInline):
    """
    Inline admin for PropertyDocument.
    """
    model = PropertyDocument
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin interface for Property model.
    """
    list_display = [
        'title', 'owner', 'category', 'listing_type', 'status',
        'city', 'sale_price', 'rent_price', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'listing_type', 'city', 'state',
        'furnished', 'pets_allowed', 'created_at'
    ]
    search_fields = ['title', 'description', 'address', 'owner__email']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'view_count',
        'inquiry_count', 'favorite_count'
    ]
    ordering = ['-created_at']
    inlines = [PropertyImageInline, PropertyDocumentInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'title', 'slug', 'description')
        }),
        (_('Ownership'), {
            'fields': ('owner', 'agent', 'created_by', 'updated_by')
        }),
        (_('Property Details'), {
            'fields': (
                'category', 'listing_type', 'status',
                'address', 'city', 'state', 'postal_code', 'country'
            )
        }),
        (_('Specifications'), {
            'fields': (
                'bedrooms', 'bathrooms', 'total_area', 'built_area',
                'lot_size', 'year_built', 'floor_number', 'total_floors'
            )
        }),
        (_('Pricing'), {
            'fields': (
                'sale_price', 'rent_price', 'price_per_unit',
                'currency', 'price_negotiable'
            )
        }),
        (_('Features'), {
            'fields': ('amenities', 'furnished', 'parking_spaces', 'pets_allowed')
        }),
        (_('Availability'), {
            'fields': ('available_from', 'minimum_lease', 'maximum_lease')
        }),
        (_('Media'), {
            'fields': ('featured_image', 'video_url', 'virtual_tour_url')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Statistics'), {
            'fields': ('view_count', 'inquiry_count', 'favorite_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_properties', 'unpublish_properties', 'mark_featured']

    @admin.action(description=_('Publish selected properties'))
    def publish_properties(self, request, queryset):
        """Publish selected properties."""
        updated = queryset.filter(status='draft').update(status='active')
        self.message_user(
            request,
            ngettext(
                '%d property was successfully published.',
                '%d properties were successfully published.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Unpublish selected properties'))
    def unpublish_properties(self, request, queryset):
        """Unpublish selected properties."""
        updated = queryset.filter(status='active').update(status='inactive')
        self.message_user(
            request,
            ngettext(
                '%d property was successfully unpublished.',
                '%d properties were successfully unpublished.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Mark as featured'))
    def mark_featured(self, request, queryset):
        """Mark properties as featured (placeholder for future feature)."""
        self.message_user(
            request,
            _('Feature marking functionality will be implemented soon.')
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Admin interface for Favorite model.
    """
    list_display = ['user', 'property', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'property__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """
    Admin interface for Inquiry model.
    """
    list_display = [
        'property', 'user', 'subject', 'is_read',
        'is_responded', 'created_at'
    ]
    list_filter = ['is_read', 'is_responded', 'created_at']
    search_fields = ['property__title', 'user__email', 'subject']
    readonly_fields = [
        'created_at', 'updated_at', 'responded_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Inquiry Information'), {
            'fields': ('property', 'user', 'subject', 'message')
        }),
        (_('Contact Details'), {
            'fields': ('email', 'phone_number')
        }),
        (_('Status'), {
            'fields': ('is_read', 'read_at', 'is_responded', 'responded_at', 'responded_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description=_('Mark selected inquiries as read'))
    def mark_as_read(self, request, queryset):
        """Mark selected inquiries as read."""
        updated = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                '%d inquiry was marked as read.',
                '%d inquiries were marked as read.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Mark selected inquiries as unread'))
    def mark_as_unread(self, request, queryset):
        """Mark selected inquiries as unread."""
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(
            request,
            ngettext(
                '%d inquiry was marked as unread.',
                '%d inquiries were marked as unread.',
                updated,
            ) % updated,
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    """
    list_display = [
        'property', 'user', 'rating', 'is_verified',
        'is_featured', 'created_at'
    ]
    list_filter = ['rating', 'is_verified', 'is_featured', 'created_at']
    search_fields = ['property__title', 'user__email', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('Review Information'), {
            'fields': ('property', 'user', 'booking', 'title', 'comment')
        }),
        (_('Rating'), {
            'fields': ('rating', 'cleanliness_rating', 'location_rating', 'value_rating', 'communication_rating')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_featured')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['verify_reviews', 'feature_reviews']

    @admin.action(description=_('Verify selected reviews'))
    def verify_reviews(self, request, queryset):
        """Verify selected reviews."""
        updated = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(
            request,
            ngettext(
                '%d review was verified.',
                '%d reviews were verified.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Feature selected reviews'))
    def feature_reviews(self, request, queryset):
        """Feature selected reviews."""
        updated = queryset.filter(is_featured=False).update(is_featured=True)
        self.message_user(
            request,
            ngettext(
                '%d review was featured.',
                '%d reviews were featured.',
                updated,
            ) % updated,
        )