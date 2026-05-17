"""
Booking models for Kirokiro.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# from apps.core.mixins import TimestampMixin


class BookingStatus(models.TextChoices):
    """Booking status choices."""

    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    CHECKED_IN = "checked_in", _("Checked In")
    CHECKED_OUT = "checked_out", _("Checked Out")
    CANCELLED = "cancelled", _("Cancelled")
    REJECTED = "rejected", _("Rejected")
    NO_SHOW = "no_show", _("No Show")


class PaymentStatus(models.TextChoices):
    """Payment status choices."""

    PENDING = "pending", _("Pending")
    PARTIAL = "partial", _("Partially Paid")
    PAID = "paid", _("Paid")
    REFUNDED = "refunded", _("Refunded")
    FAILED = "failed", _("Failed")


class Booking(models.Model):
    """
    Booking model for property rentals.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_number = models.CharField(max_length=20, unique=True, db_index=True)

    # Relationships
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    guest = models.ForeignKey(
        "kiro.User",
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    # Dates
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    actual_check_in = models.DateTimeField(null=True, blank=True)
    actual_check_out = models.DateTimeField(null=True, blank=True)

    # Guests
    number_of_guests = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    number_of_children = models.PositiveIntegerField(default=0)
    guest_names = models.TextField(blank=True, help_text="Names of additional guests")

    # Pricing
    nightly_rate = models.DecimalField(max_digits=12, decimal_places=2)
    number_of_nights = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    # Status
    status = models.CharField(
        max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    # Special requests
    special_requests = models.TextField(blank=True)
    guest_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "kiro.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_bookings",
    )
    cancellation_reason = models.TextField(blank=True)
    refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Communication
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=["booking_number"]),
            models.Index(fields=["property", "status"]),
            models.Index(fields=["guest", "status"])
        ]


class Payment(models.Model):
    """
    Payment model for booking transactions.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="payments"
    )
    user = models.ForeignKey(
        "kiro.User", on_delete=models.CASCADE, related_name="payments"
    )

    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
    payment_gateway = models.CharField(max_length=50, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
            ("refunded", "Refunded"),
        ],
        default="pending"
    )

    # Additional info
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Processing
    processed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["booking", "status"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["transaction_id"]),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"

    def mark_completed(self):
        """Mark payment as completed."""
        from django.utils import timezone
        self.status = "completed"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def mark_refunded(self, refund_amount=None):
        """Mark payment as refunded."""
        from django.utils import timezone
        self.status = "refunded"
        self.refunded_at = timezone.now()
        if refund_amount is not None:
            self.refund_amount = refund_amount
        self.save(update_fields=["status", "refunded_at", "refund_amount"])