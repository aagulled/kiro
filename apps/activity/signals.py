"""
Signals for automatic activity logging.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import ValidationError


# User authentication signals
def log_user_login(sender, request, user, **kwargs):
    """Signal receiver: log login via ActivityService with IP."""
    from apps.activity.services.activity import ActivityService
    activity_service = ActivityService()
    ip_address = activity_service._get_client_ip(request) if request else 'Unknown'
    activity_service.log_activity(
        action_type='login',
        actor=user,
        description=f"User logged in from {ip_address}",
        request=request
    )


def log_user_logout(sender, request, user, **kwargs):
    """Signal receiver: log logout via ActivityService."""
    from apps.activity.services.activity import ActivityService
    activity_service = ActivityService()
    activity_service.log_activity(
        action_type='logout',
        actor=user,
        description="User logged out",
        request=request
    )


def log_property_changes(sender, instance, **kwargs):
    """Signal receiver: log property CUD via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if instance.pk:  # Update
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            old_values = {
                'title': old_instance.title,
                'description': old_instance.description,
                'status': old_instance.status,
                'price': float(old_instance.rent_price or old_instance.sale_price or 0),
            }
            new_values = {
                'title': instance.title,
                'description': instance.description,
                'status': instance.status,
                'price': float(instance.rent_price or instance.sale_price or 0),
            }

            if old_values != new_values:
                ActivityService.log_activity(
                    action_type='property_update',
                    actor=getattr(instance, 'updated_by', None),
                    target_type='property',
                    target_id=str(instance.id),
                    target_name=instance.title,
                    description=f"Updated property '{instance.title}'",
                    old_values=old_values,
                    new_values=new_values,
                    content_object=instance
                )
        except sender.DoesNotExist:
            pass
    else:  # Create
        ActivityService.log_activity(
            action_type='property_create',
            actor=getattr(instance, 'created_by', None),
            target_type='property',
            target_id=str(instance.id),
            target_name=instance.title,
            description=f"Created property '{instance.title}'",
            content_object=instance
        )


def log_property_deletion(sender, instance, **kwargs):
    """Signal receiver: log property hard-delete via ActivityService."""
    # Note: We can't get the user who deleted it from the instance
    # This would need to be tracked separately in the view/service layer
    from apps.activity.services.activity import ActivityService
    ActivityService.log_activity(
        action_type='property_delete',
        target_type='property',
        target_id=str(instance.id),
        target_name=instance.title,
        description=f"Deleted property '{instance.title}'",
        severity='high'
    )


def log_booking_changes(sender, instance, created, **kwargs):
    """Signal receiver: log booking create/update via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if created:
        ActivityService.log_activity(
            action_type='booking_create',
            actor=instance.guest,
            target_type='booking',
            target_id=str(instance.id),
            target_name=f"Booking {instance.booking_number}",
            description=f"Created booking for '{instance.property.title}'",
            content_object=instance
        )
    else:
        # Log status changes
        ActivityService.log_activity(
            action_type=f"booking_{instance.status}",
            actor=getattr(instance, 'updated_by', instance.guest),
            target_type='booking',
            target_id=str(instance.id),
            target_name=f"Booking {instance.booking_number}",
            description=f"Booking status changed to {instance.status}",
            content_object=instance
        )


def log_payment_changes(sender, instance, created, **kwargs):
    """Signal receiver: log payment create/update via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if created:
        ActivityService.log_activity(
            action_type='payment_process',
            actor=instance.user,
            target_type='payment',
            target_id=str(instance.transaction_id),
            target_name=f"Payment {instance.transaction_id}",
            description=f"Created payment of {instance.amount} {instance.currency}",
            content_object=instance
        )
    elif instance.status == 'completed':
        ActivityService.log_activity(
            action_type='payment_process',
            actor=instance.user,
            target_type='payment',
            target_id=str(instance.transaction_id),
            target_name=f"Payment {instance.transaction_id}",
            description=f"Payment completed: {instance.amount} {instance.currency}",
            content_object=instance
        )
    elif instance.status == 'refunded':
        ActivityService.log_activity(
            action_type='payment_refund',
            actor=getattr(instance, 'refunded_by', None),
            target_type='payment',
            target_id=str(instance.transaction_id),
            target_name=f"Payment {instance.transaction_id}",
            description=f"Payment refunded: {instance.refund_amount} {instance.currency}",
            severity='high',
            content_object=instance
        )


def log_review_changes(sender, instance, created, **kwargs):
    """Signal receiver: log review create via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if created:
        ActivityService.log_activity(
            action_type='property_review',
            actor=instance.user,
            target_type='review',
            target_id=str(instance.id),
            target_name=f"Review for {instance.property.title}",
            description=f"Posted review for '{instance.property.title}' ({instance.rating} stars)",
            content_object=instance
        )


def log_inquiry_changes(sender, instance, created, **kwargs):
    """Signal receiver: log inquiry create via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if created:
        ActivityService.log_activity(
            action_type='property_inquiry',
            actor=instance.user,
            target_type='inquiry',
            target_id=str(instance.id),
            target_name=f"Inquiry about {instance.property.title}",
            description=f"Sent inquiry about '{instance.property.title}'",
            content_object=instance
        )
    elif instance.is_responded and instance.responded_by:
        ActivityService.log_activity(
            action_type='inquiry_response',
            actor=instance.responded_by,
            target_type='inquiry',
            target_id=str(instance.id),
            target_name=f"Inquiry about {instance.property.title}",
            description=f"Responded to inquiry about '{instance.property.title}'",
            content_object=instance
        )


def log_favorite_changes(sender, instance, created, **kwargs):
    """Signal receiver: log favorite create via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if created:
        ActivityService.log_activity(
            action_type='property_favorite',
            actor=instance.user,
            target_type='favorite',
            target_id=str(instance.id),
            target_name=f"Favorited {instance.property.title}",
            description=f"Added '{instance.property.title}' to favorites",
            content_object=instance
        )


def log_profile_updates(sender, instance, created, **kwargs):
    """Signal receiver: log profile update via ActivityService."""
    from apps.activity.services.activity import ActivityService
    if not created:
        ActivityService.log_activity(
            action_type='profile_update',
            actor=instance.user,
            target_type='user_profile',
            target_id=str(instance.id),
            target_name=f"Profile for {instance.user.email}",
            description="Updated user profile",
            content_object=instance
        )


# Signals are connected in the AppConfig.ready() method to avoid database access during import