"""
Custom permissions for Kirokiro.
"""
from rest_framework import permissions

# from apps.tenants.utils import get_current_tenant
def get_current_tenant():
    return None


class IsTenantUser(permissions.BasePermission):
    """
    Permission that checks if the user belongs to the current tenant.
    """

    def has_permission(self, request, view):
        # Allow superusers access to everything
        if request.user and request.user.is_superuser:
            return True

        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Get current tenant
        tenant = get_current_tenant()
        if not tenant:
            return False

        # Check if user belongs to this tenant
        return (
            hasattr(request.user, "tenant")
            and request.user.tenant == tenant
            and request.user.is_active
        )


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is a tenant admin.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers are treated as admins
        if request.user.is_superuser:
            return True

        return request.user.role == "admin" and request.user.is_active


class IsTenantAgent(permissions.BasePermission):
    """
    Permission that checks if the user is a tenant agent.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        tenant = get_current_tenant()
        if not tenant:
            return False

        return (
            hasattr(request.user, "tenant")
            and request.user.tenant == tenant
            and request.user.role in ["agent", "staff", "admin"]
            and request.user.is_active
        )


class IsTenantHost(permissions.BasePermission):
    """
    Permission that checks if the user is a tenant host.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return request.user.role in ["host", "owner", "agent", "staff", "admin"] and request.user.is_active


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that checks if the user is the owner of the object.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusers can modify anything
        if request.user.is_superuser:
            return True

        # Check ownership
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "created_by"):
            return obj.created_by == request.user

        return False


class IsTenantStaff(permissions.BasePermission):
    """
    Permission that checks if the user is tenant staff (agent or admin).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return request.user.role in ["agent", "staff", "admin"] and request.user.is_active


class IsPropertyOwner(permissions.BasePermission):
    """
    Permission that checks if the user owns the property.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # For write operations, check ownership
        return obj.owner == request.user or request.user.is_superuser


class CanManageProperty(permissions.BasePermission):
    """
    Permission that allows owners, assigned agents, and admins to manage properties.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Owner can always manage
        if obj.owner == request.user:
            return True

        # Assigned agent can manage
        if obj.agent == request.user and request.user.role in ["agent", "admin"]:
            return True

        # Admins can manage all properties
        return request.user.role == "admin"
