"""
Signals for automatic notification triggering in Kirokiro.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from apps.notifications.services.notifications import NotificationService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Post-save receiver: ensure NotificationPreference exists for new users."""
    if created:
        try:
            preferences = NotificationService.get_user_preferences(instance)
            logger.info(f"Created notification preferences for new user {instance.email}")
        except Exception as e:
            logger.exception(f"Failed to create notification preferences for user {instance.email}: {e}")


# Signal handlers will be connected in AppConfig.ready() to avoid database access during import


<<<<<<< HEAD
@receiver(post_save, sender='kiro.Payment')
=======
@receiver(post_save, sender='payment.Payment')
>>>>>>> e13cee5 (update)
def notify_payment_successful(sender, instance, created, **kwargs):
    """Post-save receiver: send payment success notification when status=completed."""
    if not created and instance.status == 'completed' and instance.user:
        try:
            NotificationService.send_notification(
                user=instance.user,
                title="Payment Successful",
                message=f"Your payment of {instance.amount} {instance.currency} has been processed successfully.",
                notification_type='payment',
                channels=['email', 'in_app', 'sms'],
                priority='high',
                content_object=instance,
            )
            logger.info(f"Sent payment success notification for payment {instance.transaction_id}")
        except Exception as e:
            logger.exception(f"Failed to send payment notification: {e}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def notify_password_changed(sender, instance, created, **kwargs):
    """Post-save receiver: notify user on password change."""
    if not created and instance.password_changed_at:
        try:
            NotificationService.send_notification(
                user=instance,
                title="Password Changed",
                message="Your password has been changed successfully. If you did not make this change, please contact support immediately.",
                notification_type='security',
                channels=['email', 'in_app', 'push'],
                priority='urgent',
                content_object=instance,
            )
            logger.info(f"Sent password change notification for user {instance.email}")
        except Exception as e:
            logger.exception(f"Failed to send password change notification: {e}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def notify_account_verified(sender, instance, created, **kwargs):
    """Post-save receiver: notify on email verification completion."""
    if not created and instance.is_verified and instance.email_verified_at:
        try:
            NotificationService.send_notification(
                user=instance,
                title="Account Verified",
                message="Congratulations! Your account has been verified successfully. You now have full access to all features.",
                notification_type='system',
                channels=['email', 'in_app'],
                priority='medium',
                content_object=instance,
            )
            logger.info(f"Sent account verification notification for user {instance.email}")
        except Exception as e:
            logger.exception(f"Failed to send account verification notification: {e}")


# Additional signal handlers can be added here for other events like:
# - Property inquiries
# - Reviews received
# - Booking cancellations
# - Admin announcements
# - System maintenance notifications