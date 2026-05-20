"""
Notification Service for Kirokiro.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for handling notifications.
    """
    
    def __init__(self):
        self.logger = logger
    
    def send_email_notification(self, recipient_email, subject, template_name, context):
        """Render template and send plain+HTML email via Django send_mail."""
        try:
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def get_user_preferences(self, user):
        """Return default preference stub (placeholder until full impl)."""
        # This is a placeholder - would normally retrieve NotificationPreference records
        # For now, return a simple object with default preferences
        class Preferences:
            email_notifications = True
            sms_notifications = False
            push_notifications = True
        
        return Preferences()
    
    def create_notification_preferences(self, user):
        """Create default NotificationPreference row for user."""
        from apps.notifications.models import NotificationPreference
        NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_notifications': True,
                'sms_notifications': False,
                'push_notifications': True,
            }
        )

    def send_notification(self, user, title, message, notification_type='system', 
                           channels=None, priority='medium', content_object=None):
        """Create Notification record and dispatch to requested channels."""
        if channels is None:
            channels = ['in_app']
            
        from apps.notifications.models import Notification
        from django.contrib.contenttypes.models import ContentType

        # Create in-app Notification record
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
        )
        if content_object:
            notification.content_type = ContentType.objects.get_for_model(content_object)
            notification.object_id = content_object.id
            notification.save()

        # Dispatch to channels
        prefs = self.get_user_preferences(user)
        if 'email' in channels and prefs.email_notifications:
            self.send_email_notification(
                user.email, title, 'emails/notification.html', {'title': title, 'message': message}
            )
        # SMS/push would integrate with external providers here

        self.logger.info(f"Notification sent: {notification_type} to {user.email}")
        return notification