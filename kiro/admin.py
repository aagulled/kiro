"""
Admin configuration for Kiro models.
"""
from django import forms
from django.contrib import admin
from .models import (
    Amenity,
    Property,
    PropertyImage,
    PropertyDocument,
    Favorite,
    Inquiry,
    Review,
<<<<<<< HEAD
    Booking,
    Payment,
=======
>>>>>>> e13cee5 (update)
    User,
)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """Admin for Amenity model with search and filters."""
    list_display = ("name", "category", "created_at")
    search_fields = ("name", "category")
    list_filter = ("category",)
    ordering = ("name",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property with amenities selection."""
    list_display = ("title", "category", "status", "city", "owner")
    search_fields = ("title", "description", "city")
    list_filter = ("category", "status", "listing_type", "country")
    filter_horizontal = ("amenities",)  # Nice multi-select for all amenities
    raw_id_fields = ("owner", "agent")


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "is_primary", "order")
    list_filter = ("is_primary",)


admin.site.register(PropertyDocument)
admin.site.register(Favorite)
admin.site.register(Inquiry)
admin.site.register(Review)
<<<<<<< HEAD
admin.site.register(Booking)
admin.site.register(Payment)
=======
>>>>>>> e13cee5 (update)
