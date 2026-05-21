"""
Consolidated models for Kirokiro.
"""
import uuid

import pycountry
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.mixins import TimestampMixin
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
        ("agent", "Agent"),
        ("staff", "Staff"),
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

    def save(self, *args, **kwargs):
        # Set is_staff for staff, agent, admin roles
        if self.role in ["staff", "agent", "admin"]:
            self.is_staff = True
        super().save(*args, **kwargs)

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





class PropertyQuerySet(models.QuerySet):
    """
    Custom queryset for Property model.
    """

    def active(self):
        """Return active properties."""
        return self.filter(status=PropertyStatus.ACTIVE, is_deleted=False)

    def available(self):
        """Return available properties."""
        return self.filter(status=PropertyStatus.ACTIVE, is_deleted=False)

    def by_owner(self, owner):
        """Return properties owned by a user."""
        return self.filter(owner=owner, is_deleted=False)

    def by_agent(self, agent):
        """Return properties assigned to an agent."""
        return self.filter(agent=agent, is_deleted=False)

    def for_sale(self):
        """Return properties for sale."""
        return self.filter(
            listing_type__in=[ListingType.SALE, ListingType.BOTH],
            status=PropertyStatus.ACTIVE,
            is_deleted=False
        )

    def for_rent(self):
        """Return properties for rent."""
        return self.filter(
            listing_type__in=[ListingType.RENT, ListingType.BOTH],
            status=PropertyStatus.ACTIVE,
            is_deleted=False
        )

    def in_city(self, city):
        """Return properties in a specific city."""
        return self.filter(city__iexact=city, is_deleted=False)

    def with_related(self):
        """Return properties with related data."""
        return self.select_related("owner", "agent").prefetch_related("images", "amenities")


class PropertyManager(models.Manager):
    """
    Custom manager for Property model.
    """

    def get_queryset(self):
        return PropertyQuerySet(self.model, using=self._db)


class PropertyCategory(models.TextChoices):
    """Property category choices."""

    APARTMENT = "apartment", _("Apartment")
    HOUSE = "house", _("House")
    VILLA = "villa", _("Villa")
    CONDO = "condo", _("Condominium")
    TOWNHOUSE = "townhouse", _("Townhouse")
    STUDIO = "studio", _("Studio")
    LOFT = "loft", _("Loft")
    PENTHOUSE = "penthouse", _("Penthouse")
    COMMERCIAL = "commercial", _("Commercial")
    LAND = "land", _("Land")
    CAMPING_SITE = "camping_site", _("Camping Site")
<<<<<<< HEAD
=======
    HOTEL_ROOM = "hotel_room", _("Hotel Room")
>>>>>>> 39a4b62 (Initial commit)
    OTHER = "other", _("Other")


class PropertyStatus(models.TextChoices):
    """Property status choices."""

    DRAFT = "draft", _("Draft")
    PENDING = "pending", _("Pending Approval")
    ACTIVE = "active", _("Active")
    RENTED = "rented", _("Rented")
    SOLD = "sold", _("Sold")
    INACTIVE = "inactive", _("Inactive")
    REJECTED = "rejected", _("Rejected")


class ListingType(models.TextChoices):
    """Listing type choices."""

    SALE = "sale", _("For Sale")
    RENT = "rent", _("For Rent")
    BOTH = "both", _("For Sale or Rent")


class Amenity(models.Model):
    """
    Amenity model for properties.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name


class Property(models.Model):
    objects = PropertyManager.from_queryset(PropertyQuerySet)()
    """
    Property listing model.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kiro_created_properties",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kiro_updated_properties",
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kiro_deleted_properties",
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()

    # Property details
    category = models.CharField(
        max_length=20, choices=PropertyCategory.choices, default=PropertyCategory.APARTMENT
    )
    listing_type = models.CharField(
        max_length=10, choices=ListingType.choices, default=ListingType.RENT
    )
    status = models.CharField(
        max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.ACTIVE
    )

    # Location
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(
        max_length=2, choices=COUNTRY_CHOICES, default="SO"
    )
    # location = gis_models.PointField(geography=True, null=True, blank=True)

    # Property specifications
    bedrooms = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, validators=[MinValueValidator(0)]
    )
    bathrooms = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, validators=[MinValueValidator(0)]
    )
    total_area = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    built_area = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    lot_size = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    year_built = models.PositiveIntegerField(null=True, blank=True)
    floor_number = models.IntegerField(null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)

    # Pricing
    sale_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    rent_price = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    price_per_unit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default="USD")
    price_negotiable = models.BooleanField(default=False)

    # Features
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")
    furnished = models.BooleanField(default=False)
    parking_spaces = models.PositiveIntegerField(default=0)
    pets_allowed = models.BooleanField(default=False)

    # Availability
    available_from = models.DateField(null=True, blank=True)
    minimum_lease = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum lease in months")
    maximum_lease = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum lease in months")

    # Media
    featured_image = models.ImageField(upload_to="properties/featured/", blank=True)
    video_url = models.URLField(blank=True)
    virtual_tour_url = models.URLField(blank=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    # Statistics
    view_count = models.PositiveIntegerField(default=0)
    inquiry_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    # Owner/Agent
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="kiro_owned_properties",
        null=True,
        blank=True,
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="kiro_assigned_properties",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["listing_type"]),
            models.Index(fields=["city", "state"]),
            models.Index(fields=["sale_price"]),
            models.Index(fields=["rent_price"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def display_price(self):
        """Return the appropriate price based on listing type."""
        if self.listing_type == ListingType.SALE and self.sale_price:
            return self.sale_price
        elif self.listing_type == ListingType.RENT and self.rent_price:
            return self.rent_price
        return self.sale_price or self.rent_price

    @property
    def is_available(self):
        """Check if property is available."""
        return self.status == PropertyStatus.ACTIVE

    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=["view_count"])

    def clean(self):
        """Validate property data."""
        if self.year_built and self.year_built > timezone.now().year:
            raise ValidationError("Year built cannot be in the future.")

        if self.total_area and self.built_area and self.built_area > self.total_area:
            raise ValidationError("Built area cannot exceed total area.")

        if self.lot_size and self.total_area and self.lot_size < self.total_area:
            raise ValidationError("Lot size cannot be smaller than total area.")

        if self.floor_number and self.total_floors and self.floor_number > self.total_floors:
            raise ValidationError("Floor number cannot exceed total floors.")



    def increment_inquiry_count(self):
        """Increment inquiry count."""
        self.inquiry_count += 1
        self.save(update_fields=["inquiry_count"])


class PropertyImage(models.Model):
    """
    Property image model.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="properties/images/")
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Property Image"
        verbose_name_plural = "Property Images"

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyDocument(models.Model):
    """
    Property document model.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    DOCUMENT_TYPES = [
        ("deed", "Property Deed"),
        ("survey", "Property Survey"),
        ("inspection", "Inspection Report"),
        ("disclosure", "Seller Disclosure"),
        ("tax", "Tax Records"),
        ("insurance", "Insurance"),
        ("other", "Other"),
    ]

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="documents"
    )
    document = models.FileField(upload_to="properties/documents/")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Property Document"
        verbose_name_plural = "Property Documents"

    def __str__(self):
        return f"{self.title} - {self.property.title}"


class Favorite(models.Model):
    """
    User favorite properties.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kiro_favorites"
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="favorited_by"
    )

    class Meta:
        unique_together = ["user", "property"]
        ordering = ["-created_at"]
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"

    def __str__(self):
        return f"{self.user.email} - {self.property.title}"


class Inquiry(models.Model):
    """
    Property inquiry model for user questions about properties.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="inquiries"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kiro_inquiries"
    )

    # Inquiry details
    subject = models.CharField(max_length=255)
    message = models.TextField()
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_responded = models.BooleanField(default=False)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kiro_responded_inquiries",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Inquiry"
        verbose_name_plural = "Inquiries"
        indexes = [
            models.Index(fields=["property", "is_read"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"Inquiry about {self.property.title} by {self.user.email}"

    def mark_as_read(self):
        """Mark inquiry as read."""
        self.is_read = True
        self.save(update_fields=["is_read"])

    def mark_as_responded(self, responder):
        """Mark inquiry as responded."""
        from django.utils import timezone
        self.is_responded = True
        self.responded_at = timezone.now()
        self.responded_by = responder
        self.save(update_fields=["is_responded", "responded_at", "responded_by"])


class Review(models.Model):
    """
    Property review and rating model.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kiro_reviews"
    )
    booking = models.OneToOneField(
        "Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review",
    )

    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)

    # Review aspects
    cleanliness_rating = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    location_rating = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    value_rating = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication_rating = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Status
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ["property", "user"]
        indexes = [
            models.Index(fields=["property", "rating"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"Review for {self.property.title} by {self.user.email} - {self.rating} stars"

    def get_average_aspect_rating(self):
        """Calculate average of aspect ratings."""
        ratings = [
            self.cleanliness_rating,
            self.location_rating,
            self.value_rating,
            self.communication_rating,
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None


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
        Property,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    guest = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="kiro_bookings",
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kiro_cancelled_bookings",
    )
    cancellation_reason = models.TextField(blank=True)
    refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Communication
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    def clean(self):
        """Validate booking data."""
        if self.check_out_date <= self.check_in_date:
            raise ValidationError("Check-out date must be after check-in date.")

        if self.check_in_time and self.check_out_time:
            # If same day, check times
            if self.check_in_date == self.check_out_date and self.check_out_time <= self.check_in_time:
                raise ValidationError("Check-out time must be after check-in time on the same day.")

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
    Payment model for booking transactions with commission.
    """

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="payments"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="booking_payments"
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


