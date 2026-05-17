"""
Tenant utilities for Kirokiro.
"""
from django.db import connection

from .models import Tenant


def get_current_tenant():
    """
    Get the current tenant from the database schema.
    """
    schema_name = connection.schema_name
    if schema_name == "public":
        return None
    try:
        return Tenant.objects.get(schema_name=schema_name)
    except Tenant.DoesNotExist:
        return None


def set_tenant_schema(tenant):
    """
    Set the database schema for the given tenant.
    """
    connection.set_schema(tenant.schema_name)


def get_tenant_by_domain(domain):
    """
    Get tenant by domain name.
    """
    from .models import Domain

    try:
        domain_obj = Domain.objects.select_related("tenant").get(domain=domain)
        return domain_obj.tenant
    except Domain.DoesNotExist:
        return None
