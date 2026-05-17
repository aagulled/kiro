"""
Serializers for tenants app.
"""
from rest_framework import serializers

from .models import Domain, Tenant


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model.
    """

    is_paid = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "plan",
            "is_active",
            "paid_until",
            "on_trial",
            "is_paid",
            "contact_email",
            "contact_phone",
            "address",
            "logo",
            "primary_color",
            "secondary_color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_paid"]


class TenantCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new tenant.
    """

    domain = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Tenant
        fields = [
            "name",
            "slug",
            "description",
            "plan",
            "contact_email",
            "contact_phone",
            "address",
            "domain",
        ]

    def create(self, validated_data):
        domain = validated_data.pop("domain")
        tenant = Tenant.objects.create(**validated_data)
        Domain.objects.create(tenant=tenant, domain=domain, is_primary=True)
        return tenant


class DomainSerializer(serializers.ModelSerializer):
    """
    Serializer for Domain model.
    """

    class Meta:
        model = Domain
        fields = ["id", "domain", "is_primary", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
