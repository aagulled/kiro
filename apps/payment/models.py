"""
Payment models for Kirokiro.
"""
import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentQuerySet(models.QuerySet):
    """
    Custom queryset for Payment model.
    """

    def completed(self):
        """Return completed payments."""
        return self.filter(status="completed")

    def pending(self):
        """Return pending payments."""
        return self.filter(status="pending")

    def failed(self):
        """Return failed payments."""
        return self.filter(status="failed")

    def refunded(self):
        """Return refunded payments."""
        return self.filter(status="refunded")

    def by_user(self, user):
        """Return payments by user."""
        return self.filter(user=user)

    def by_booking(self, booking):
        """Return payments by booking."""
        return self.filter(booking=booking)


class Payment(models.Model):
    """
    Payment model for booking transactions with commission.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    booking = models.ForeignKey(
        'kiro.Booking', on_delete=models.CASCADE, related_name="app_payments"
    )
    user = models.ForeignKey(
        'kiro.User', on_delete=models.CASCADE, related_name="app_user_payments"
    )

    PAYMENT_METHOD_CHOICES = [
        ("card", "Card Payment"),
        ("mobile_money", "Mobile Money"),
    ]

    PROVIDER_CHOICES = [
        ("golis", "Golis"),
        ("hormuud", "Hormuud Telecom"),
        ("telesom", "Telesom"),
        ("somtel", "Somtel"),
        ("amtelt", "Amtel"),
    ]

    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="mobile_money"
    )
    provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, default="golis", blank=True
    )
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

    objects = PaymentQuerySet.as_manager()

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
        return f"Payment {self.transaction_id} - {self.amount + self.commission_amount} {self.currency}"

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