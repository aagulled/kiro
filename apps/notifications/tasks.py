"""
Celery tasks for asynchronous notification delivery.
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services.notifications import NotificationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, notification_id):
    """
    Asynchronous task to deliver a notification.

    Args:
        notification_id: UUID of the notification to deliver

    Returns:
        bool: True if delivery was successful
    """
    try:
        notification = Notification.objects.get(id=notification_id)

        # Skip if already delivered
        if notification.is_delivered:
            logger.info(f"Notification {notification_id} already delivered, skipping")
            return True

        # Attempt delivery
        success = NotificationService._deliver_notification(notification)

        if not success:
            # Retry logic
            if self.request.retries < self.max_retries:
                logger.warning(f"Notification delivery failed for {notification_id}, retrying...")
                raise self.retry()
            else:
                logger.error(f"Notification delivery failed permanently for {notification_id}")
                return False

        logger.info(f"Successfully delivered notification {notification_id}")
        return True

    except ObjectDoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in send_notification_task for {notification_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry()
        return False


@shared_task
def send_bulk_notifications_task(notification_ids):
    """
    Send multiple notifications asynchronously.

    Args:
        notification_ids: List of notification UUIDs to deliver

    Returns:
        dict: Results of delivery attempts
    """
    results = {
        'successful': [],
        'failed': [],
        'total': len(notification_ids)
    }

    for notification_id in notification_ids:
        try:
            success = send_notification_task.delay(notification_id).get(timeout=30)
            if success:
                results['successful'].append(str(notification_id))
            else:
                results['failed'].append(str(notification_id))
        except Exception as e:
            logger.exception(f"Failed to process notification {notification_id}: {e}")
            results['failed'].append(str(notification_id))

    logger.info(f"Bulk notification results: {results['total']} total, {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results


@shared_task
def send_digest_notifications_task(user_id, frequency='daily'):
    """
    Send digest notifications to users based on their frequency preference.

    Args:
        user_id: User ID to send digest to
        frequency: Digest frequency ('daily' or 'weekly')

    Returns:
        bool: True if digest was sent successfully
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=user_id)
        preferences = NotificationService.get_user_preferences(user)

        # Only send if user has digest frequency preference
        if preferences.notification_frequency != frequency:
            logger.info(f"User {user.email} has {preferences.notification_frequency} preference, skipping {frequency} digest")
            return True

        # Get unread notifications for digest
        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=1 if frequency == 'daily' else 7)
        ).order_by('-created_at')

        if not unread_notifications.exists():
            logger.info(f"No unread notifications for {frequency} digest to user {user.email}")
            return True

        # Create digest notification
        count = unread_notifications.count()
        title = f"Daily Digest" if frequency == 'daily' else "Weekly Digest"
        message = f"You have {count} unread notifications. Check your notifications for details."

        NotificationService.send_notification(
            user=user,
            title=title,
            message=message,
            notification_type='system',
            channels=preferences.get_enabled_channels(),
            priority='low',
            metadata={'digest_type': frequency, 'notification_count': count},
            async_delivery=False
        )

        logger.info(f"Sent {frequency} digest with {count} notifications to user {user.email}")
        return True

    except Exception as e:
        logger.exception(f"Failed to send {frequency} digest to user {user_id}: {e}")
        return False


@shared_task
def cleanup_old_notifications_task(days=30):
    """
    Clean up old read notifications.

    Args:
        days: Number of days after which to delete read notifications

    Returns:
        int: Number of notifications deleted
    """
    try:
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old notifications older than {days} days")
        return deleted_count

    except Exception as e:
        logger.exception(f"Failed to cleanup old notifications: {e}")
        return 0


@shared_task
def retry_failed_notifications_task(max_attempts=3):
    """
    Retry delivery of failed notifications.

    Args:
        max_attempts: Maximum delivery attempts allowed

    Returns:
        dict: Results of retry attempts
    """
    try:
        failed_notifications = Notification.objects.filter(
            delivered=False,
            delivery_attempts__lt=max_attempts
        ).exclude(delivery_error='')

        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0
        }

        for notification in failed_notifications:
            results['processed'] += 1
            success = send_notification_task.delay(notification.id).get(timeout=30)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1

        logger.info(f"Retry results: {results}")
        return results

    except Exception as e:
        logger.exception(f"Failed to retry failed notifications: {e}")
        return {'error': str(e)}