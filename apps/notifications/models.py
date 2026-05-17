"""
Notification models for Kirokiro.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import TimestampMixin


class NotificationPreference(models.Model):
    """
    Per-user notification channel and type frequency settings.
    """

    FREQUENCY_CHOICES = [
        ('instant', _('Instant')),
        ('daily', _('Daily Digest')),
        ('weekly', _('Weekly Digest')),
    ]

    # Relationship to User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Channel preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_("Enable email notifications")
    )
    sms_notifications = models.BooleanField(
        default=False,
        help_text=_("Enable SMS notifications")
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text=_("Enable push notifications")
    )
    in_app_notifications = models.BooleanField(
        default=True,
        help_text=_("Enable in-app notifications")
    )

    # Notification frequency (for digest channels)
    notification_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='instant',
        help_text=_("Notification delivery frequency")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Notification Preference")
        verbose_name_plural = _("Notification Preferences")
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        """Return preference owner email for admin display."""
        return f"Preferences for {self.user.email}"

    def is_channel_enabled(self, channel):
        """Return True if given channel (email/sms/push/in_app) is enabled."""
        channel_map = {
            'email': self.email_notifications,
            'sms': self.sms_notifications,
            'push': self.push_notifications,
            'in_app': self.in_app_notifications,
        }
        return channel_map.get(channel, False)

    def get_enabled_channels(self):
        """Return list of currently enabled notification channels."""
        channels = []
        if self.email_notifications:
            channels.append('email')
        if self.sms_notifications:
            channels.append('sms')
        if self.push_notifications:
            channels.append('push')
        if self.in_app_notifications:
            channels.append('in_app')
        return channels


class Notification(models.Model):
    """
    User notification record with type/priority/read status and metadata.
    """

    CHANNEL_CHOICES = [
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('push', _('Push Notification')),
        ('in_app', _('In-App Notification')),
        ('whatsapp', _('WhatsApp')),  # For future extensibility
    ]

    TYPE_CHOICES = [
        ('system', _('System Notification')),
        ('property_listing', _('Property Listing Update')),
        ('payment', _('Payment Confirmation')),
        ('booking', _('Booking Alert')),
        ('admin', _('Admin Announcement')),
        ('security', _('Security Alert')),
        ('marketing', _('Marketing')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_system_notifications'
    )

    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system'
    )

    # Delivery information
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default='in_app'
    )

    # Status and tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Delivery tracking
    delivered = models.BooleanField(default=False)
    delivery_attempts = models.PositiveIntegerField(default=0)
    last_delivery_attempt = models.DateTimeField(null=True, blank=True)
    delivery_error = models.TextField(blank=True)

    # Priority and scheduling
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # Related object (for generic relations)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_system_notifications'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'channel']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

    def mark_as_read(self):
        """Set is_read=True and timestamp if not already read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_delivered(self):
        """Mark delivered=True and set sent_at timestamp."""
        from django.utils import timezone
        self.delivered = True
        self.sent_at = timezone.now()
        self.save(update_fields=['delivered', 'sent_at'])

    def record_delivery_attempt(self, error=None):
        """Increment attempt counter, set last_attempt time, optionally store error."""
        from django.utils import timezone
        self.delivery_attempts += 1
        self.last_delivery_attempt = timezone.now()
        if error:
            self.delivery_error = error
        self.save(update_fields=['delivery_attempts', 'last_delivery_attempt', 'delivery_error'])

    @property
    def is_delivered(self):
        """Return True if delivered flag and sent_at are both set."""
        return self.delivered and self.sent_at is not None

    @property
    def content_object(self):
        """Return related GenericForeignKey object or None."""
        if self.content_type and self.object_id:
            return self.content_type.get_object_for_this_type(pk=self.object_id)
        return None