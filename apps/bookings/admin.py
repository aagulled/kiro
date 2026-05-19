"""
Django admin configuration for bookings app.
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext

from apps.bookings.models import Booking, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for Booking model.
    """
    list_display = [
        'booking_number', 'property', 'guest', 'status',
        'check_in_date', 'check_out_date', 'total_amount', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'check_in_date', 'check_out_date', 'created_at'
    ]
    search_fields = [
        'booking_number', 'property__title', 'guest__email',
        'guest__first_name', 'guest__last_name'
    ]
    readonly_fields = [
        'id', 'booking_number', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Booking Information'), {
            'fields': ('id', 'booking_number', 'property', 'guest')
        }),
        (_('Dates'), {
            'fields': ('check_in_date', 'check_out_date', 'check_in_time', 'check_out_time')
        }),
        (_('Actual Stay'), {
            'fields': ('actual_check_in', 'actual_check_out'),
            'classes': ('collapse',)
        }),
        (_('Guests'), {
            'fields': ('number_of_guests', 'number_of_children', 'guest_names')
        }),
        (_('Pricing'), {
            'fields': (
                'nightly_rate', 'number_of_nights', 'subtotal',
                'cleaning_fee', 'service_fee', 'tax_amount',
                'discount_amount', 'total_amount', 'currency'
            )
        }),
        (_('Status'), {
            'fields': ('status', 'payment_status')
        }),
        (_('Requests & Notes'), {
            'fields': ('special_requests', 'guest_notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        (_('Cancellation'), {
            'fields': ('cancelled_at', 'cancelled_by', 'cancellation_reason', 'refund_amount'),
            'classes': ('collapse',)
        }),
        (_('Communication'), {
            'fields': ('confirmation_sent', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirm_bookings', 'cancel_bookings', 'send_reminders']

    @admin.action(description=_('Confirm selected bookings'))
    def confirm_bookings(self, request, queryset):
        """Confirm selected bookings."""
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(
            request,
            ngettext(
                '%d booking was confirmed.',
                '%d bookings were confirmed.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Cancel selected bookings'))
    def cancel_bookings(self, request, queryset):
        """Cancel selected bookings."""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(
            status='cancelled',
            cancelled_at=timezone.now(),
            cancelled_by=request.user
        )
        self.message_user(
            request,
            ngettext(
                '%d booking was cancelled.',
                '%d bookings were cancelled.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Send reminders for selected bookings'))
    def send_reminders(self, request, queryset):
        """Send reminders for upcoming bookings."""
        # This would integrate with notification system
        updated = queryset.filter(reminder_sent=False).update(reminder_sent=True)
        self.message_user(
            request,
            ngettext(
                'Reminder sent for %d booking.',
                'Reminders sent for %d bookings.',
                updated,
            ) % updated,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment model.
    """
    list_display = [
        'booking', 'user', 'amount', 'currency', 'status',
        'transaction_id', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'created_at', 'processed_at'
    ]
    search_fields = [
        'booking__booking_number', 'user__email', 'transaction_id'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'processed_at', 'refunded_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Payment Information'), {
            'fields': ('id', 'booking', 'user', 'amount', 'currency')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'transaction_id', 'payment_gateway')
        }),
        (_('Status'), {
            'fields': ('status', 'processed_at')
        }),
        (_('Refunds'), {
            'fields': ('refunded_at', 'refund_amount'),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_completed', 'mark_refunded']

    @admin.action(description=_('Mark selected payments as completed'))
    def mark_completed(self, request, queryset):
        """Mark selected payments as completed."""
        updated = 0
        for payment in queryset.filter(status__in=['pending', 'processing']):
            payment.mark_completed()
            updated += 1

        self.message_user(
            request,
            ngettext(
                '%d payment was marked as completed.',
                '%d payments were marked as completed.',
                updated,
            ) % updated,
        )

    @admin.action(description=_('Mark selected payments as refunded'))
    def mark_refunded(self, request, queryset):
        """Mark selected payments as refunded."""
        updated = 0
        for payment in queryset.filter(status='completed'):
            payment.mark_refunded()
            updated += 1

        self.message_user(
            request,
            ngettext(
                '%d payment was marked as refunded.',
                '%d payments were marked as refunded.',
                updated,
            ) % updated,
        )