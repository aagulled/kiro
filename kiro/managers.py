"""
Custom user manager for Kirokiro.
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        """
        Return only active users by default.
        """
        return super().get_queryset().filter(is_deleted=False)

    def active(self):
        """
        Return active users.
        """
        return self.filter(is_active=True)

    def by_tenant(self, tenant):
        """
        Return users belonging to a specific tenant.
        """
        return self.filter(tenant=tenant)

    def by_role(self, role):
        """
        Return users with a specific role.
        """
        return self.filter(role=role)

    def verified(self):
        """
        Return verified users.
        """
        return self.filter(is_verified=True)

    def staff_users(self):
        """
        Return staff users (agents and admins).
        """
        return self.filter(role__in=["agent", "admin"])

    def host_users(self):
        """
        Return host users.
        """
        return self.filter(role__in=["host", "agent", "admin"])

    def locked_users(self):
        """
        Return locked users.
        """
        from django.utils import timezone
        return self.filter(locked_until__gt=timezone.now())