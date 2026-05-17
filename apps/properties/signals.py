"""
Signals for properties app.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Property


@receiver(pre_save, sender=Property)
def property_pre_save(sender, instance, **kwargs):
    """Signal to handle property pre-save operations."""
    if instance.pk:
        # Get the existing instance
        old_instance = Property.objects.get(pk=instance.pk)

        # Track status changes for notifications
        if old_instance.status != instance.status:
            instance._status_changed = True
            instance._old_status = old_instance.status
        else:
            instance._status_changed = False


@receiver(post_save, sender=Property)
def property_post_save(sender, instance, created, **kwargs):
    """Signal to handle property post-save operations."""
    if created:
        # New property created - could send notification to agent/admin
        pass
    else:
        # Property updated
        if getattr(instance, '_status_changed', False):
            # Status changed - handle notifications, etc.
            # For now, just log it (in production, use proper logging)
            print(f"Property {instance.title} status changed from {instance._old_status} to {instance.status}")

    # Clean up temporary attributes
    if hasattr(instance, '_status_changed'):
        delattr(instance, '_status_changed')
    if hasattr(instance, '_old_status'):
        delattr(instance, '_old_status')