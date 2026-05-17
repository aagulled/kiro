"""
User models for Kirokiro.
"""
import uuid

import pycountry
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# from apps.core.mixins import TimestampMixin

from .managers import UserManager


# Country choices
COUNTRY_CHOICES = sorted(
    [(country.alpha_2, country.name) for country in pycountry.countries],
    key=lambda x: x[1]
)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with multi-tenancy support.
    """

    ROLE_CHOICES = [
        ("guest", "Guest"),
        ("host", "Host"),
        ("owner", "Owner"),
        ("staff", "Staff"),
        ("agent", "Agent"),
        ("admin", "Admin"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("prefer_not_to_say", "Prefer not to say"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="user_avatars/", blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, choices=GENDER_CHOICES, blank=True
    )

    # Role and tenant
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="guest")
    # tenant = models.ForeignKey(
    #     "tenants.Tenant",
    #     on_delete=models.CASCADE,
    #     related_name="users",
    #     null=True,
    #     blank=True,
    # )

    # class Meta:
    #     constraints = [
    #         models.CheckConstraint(
    #             check=(
    #                 models.Q(is_superuser=True, tenant__isnull=True) |
    #                 models.Q(is_superuser=False, tenant__isnull=False)
    #             ),
    #             name="superuser_no_tenant_regular_user_has_tenant"
    #         )
    #     ]

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status fields
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    # Security fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)

    # Preferences
    preferred_language = models.CharField(max_length=10, default="en")
    preferred_currency = models.CharField(max_length=3, default="USD")
    timezone = models.CharField(max_length=50, default="UTC")

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            # models.Index(fields=["tenant", "role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_locked(self):
        """Check if account is locked."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    @property
    def is_tenant_admin(self):
        """Check if user is a tenant admin."""
        return self.role == "admin" or self.is_superuser

    @property
    def is_tenant_agent(self):
        """Check if user is a tenant agent."""
        return self.role in ["agent", "staff", "admin"] or self.is_superuser

    @property
    def is_tenant_host(self):
        """Check if user is a tenant host."""
        return self.role in ["host", "owner", "agent", "staff", "admin"] or self.is_superuser

    def verify_email(self):
        """Mark email as verified."""
        self.is_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=["is_verified", "email_verified_at"])

    def verify_phone(self):
        """Mark phone as verified."""
        self.phone_verified_at = timezone.now()
        self.save(update_fields=["phone_verified_at"])

    def update_last_login(self, ip_address=None):
        """Update last login timestamp and IP."""
        self.last_login = timezone.now()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=["last_login", "last_login_ip", "failed_login_attempts", "locked_until"])

    def record_failed_login(self):
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=["failed_login_attempts", "locked_until"])


class UserProfile(models.Model):
    """
    Extended user profile information.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=2, choices=COUNTRY_CHOICES, default="SO", blank=True
    )

    # Identity verification
    id_document_type = models.CharField(max_length=50, blank=True)
    id_document_number = models.CharField(max_length=100, blank=True)
    id_verified = models.BooleanField(default=False)
    id_verified_at = models.DateTimeField(null=True, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    # Social links
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)

    # Additional info
    occupation = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.user.email}"


class Message(models.Model):
    """
    Message model for user-to-user communication.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )

    # Message content
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Thread support
    thread_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    # Attachments (optional)
    attachments = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=["sender", "is_read"]),
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["thread_id", "created_at"]),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} to {self.recipient.email}"

    def mark_as_read(self):
        """Mark message as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @property
    def is_thread_starter(self):
        """Check if this is the first message in a thread."""
        return self.parent_message is None

    @property
    def thread_messages(self):
        """Get all messages in this thread."""
        return Message.objects.filter(thread_id=self.thread_id).order_by("created_at")


class Notification(models.Model):
    """
    Notification model for user notifications.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )

    # Notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ("booking_request", "Booking Request"),
            ("booking_confirmed", "Booking Confirmed"),
            ("booking_cancelled", "Booking Cancelled"),
            ("payment_received", "Payment Received"),
            ("review_received", "Review Received"),
            ("inquiry_received", "Inquiry Received"),
            ("message_received", "Message Received"),
            ("property_featured", "Property Featured"),
            ("system", "System Notification"),
        ],
        default="system"
    )

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Related object (generic relation)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Delivery
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    # Priority
    priority = models.CharField(
        max_length=10,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        default="medium"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
