"""
Tenant models for Kirokiro.
"""
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from apps.core.mixins import TimestampMixin


class Tenant(TenantMixin, TimestampMixin):
    """
    Tenant model representing an organization.
    """

    PLAN_CHOICES = [
        ("free", "Free"),
        ("basic", "Basic"),
        ("premium", "Premium"),
        ("enterprise", "Enterprise"),
    ]

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    is_active = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=False)

    # Contact information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    # Branding
    logo = models.ImageField(upload_to="tenant_logos/", blank=True)
    primary_color = models.CharField(max_length=7, default="#3B82F6")
    secondary_color = models.CharField(max_length=7, default="#10B981")

    # auto_create_schema is inherited from TenantMixin
    auto_create_schema = True

    class Meta:
        ordering = ["name"]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return self.name

    @property
    def is_paid(self):
        """Check if tenant has an active paid plan."""
        if self.plan == "free":
            return False
        if self.paid_until:
            from datetime import date

            return self.paid_until >= date.today()
        return True


class Domain(DomainMixin, TimestampMixin):
    """
    Domain model for tenant.
    """

    is_primary = models.BooleanField(default=True)

    class Meta:
        ordering = ["domain"]
        verbose_name = "Domain"
        verbose_name_plural = "Domains"

    def __str__(self):
        return self.domain
