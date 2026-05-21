"""
Property models for Kirokiro.
"""

import uuid

import pycountry

# from django.contrib.gis.db import models as gis_models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Country choices
COUNTRY_CHOICES = sorted(
    [(country.alpha_2, country.name) for country in pycountry.countries],
    key=lambda x: x[1],
)

# from apps.core.mixins import AuditMixin, SoftDeleteMixin, TimestampMixin


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
            is_deleted=False,
        )

    def for_rent(self):
        """Return properties for rent."""
        return self.filter(
            listing_type__in=[ListingType.RENT, ListingType.BOTH],
            status=PropertyStatus.ACTIVE,
            is_deleted=False,
        )

    def in_city(self, city):
        """Return properties in a specific city."""
        return self.filter(city__iexact=city, is_deleted=False)

    def with_related(self):
        """Return properties with related data."""
        return self.select_related("owner", "agent").prefetch_related(
            "images", "amenities"
        )


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
        "kiro.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_properties",
    )
    updated_by = models.ForeignKey(
        "kiro.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_properties",
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "kiro.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_properties",
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()

    # Property details
    category = models.CharField(
        max_length=20,
        choices=PropertyCategory.choices,
        default=PropertyCategory.APARTMENT,
    )
    listing_type = models.CharField(
        max_length=10, choices=ListingType.choices, default=ListingType.RENT
    )
    status = models.CharField(
        max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.DRAFT
    )

    # Location
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default="SO")
    # location = gis_models.PointField(geography=True, null=True, blank=True)

    # Property specifications
    bedrooms = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, validators=[MinValueValidator(0)]
    )
    bathrooms = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, validators=[MinValueValidator(0)]
    )
    total_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    built_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    lot_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    year_built = models.PositiveIntegerField(null=True, blank=True)
    floor_number = models.IntegerField(null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)

    # Pricing
    sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    rent_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    price_per_unit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
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
    minimum_lease = models.PositiveIntegerField(
        null=True, blank=True, help_text="Minimum lease in months"
    )
    maximum_lease = models.PositiveIntegerField(
        null=True, blank=True, help_text="Maximum lease in months"
    )

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
        "kiro.User",
        on_delete=models.CASCADE,
        related_name="owned_properties",
        null=True,
        blank=True,
    )
    agent = models.ForeignKey(
        "kiro.User",
        on_delete=models.SET_NULL,
        related_name="assigned_properties",
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
        "kiro.User", on_delete=models.CASCADE, related_name="favorites"
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
        "kiro.User", on_delete=models.CASCADE, related_name="inquiries"
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
        "kiro.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responded_inquiries",
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
        "kiro.User", on_delete=models.CASCADE, related_name="property_reviews"
    )
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review",
    )

    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars",
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
