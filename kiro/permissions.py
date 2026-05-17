"""
Custom permissions for Kiro API.
"""
from rest_framework.permissions import BasePermission


class IsGuestOrReadOnly(BasePermission):
    """
    Allow guests to read only, authenticated non-guests can modify.
    """

    def has_permission(self, request, view):
        # Allow read access to everyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # For write operations, require authentication and not guest role
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role != 'guest'
        )


class IsBookingParticipant(BasePermission):
    """
    Allow access to bookings only for participants (guest or property owner) or staff.
    """

    def has_object_permission(self, request, view, obj):
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is the booking guest or property owner
        return (
            obj.guest == request.user or 
            obj.property.owner == request.user
        )


class IsOwnerOrStaff(BasePermission):
    """
    Allow property owners to modify their properties, staff have full access.
    """

    def has_object_permission(self, request, view, obj):
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Property owners can modify their properties
        return obj.owner == request.user


class PropertyPermissions(BasePermission):
    """
    Combined permissions for properties: read for all, write for authenticated non-guests, object edit for owners/staff.
    """

    def has_permission(self, request, view):
        # Allow read access to everyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # For write operations, require authentication and not guest role
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role != 'guest'
        )

    def has_object_permission(self, request, view, obj):
        # For read operations, allow anyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Staff and superusers have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Property owners can modify their properties
        return obj.owner == request.user