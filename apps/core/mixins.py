"""
Mixins for Kirokiro models.
"""
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    """
    Mixin that adds created_at and updated_at fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin that adds soft delete functionality.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_%(class)s",
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Mark record deleted without removing row from DB."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self):
        """Undo soft deletion, clearing deletion metadata."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def hard_delete(self):
        """Bypass soft-delete and remove row permanently."""
        super().delete()

    def delete(self, *args, **kwargs):
        """Override delete to perform soft delete by default."""
        force = kwargs.pop("force", False)
        user = kwargs.pop("user", None)
        if force:
            self.hard_delete()
        else:
            self.soft_delete(user)


class AuditMixin(models.Model):
    """
    Mixin that adds audit fields (created_by, updated_by).
    """

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
    )
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s",
    )

    class Meta:
        abstract = True





class VersionedResponseMixin:
    """
    Mixin to add API version to responses.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['X-API-Version'] = 'v1'
        return response
