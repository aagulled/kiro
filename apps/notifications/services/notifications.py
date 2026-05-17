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
        """Create default NotificationPreference row for user (stub)."""
        # This is a placeholder - would normally create NotificationPreference records
        pass
        
    def send_notification(self, user, title, message, notification_type='system', 
                          channels=None, priority='medium', content_object=None):
        """Create Notification record and dispatch to requested channels (stub)."""
        if channels is None:
            channels = ['in_app']
            
        # Log the notification attempt
        self.logger.info(f"Sending {notification_type} notification to user {user.email}: {title}")
        
        # In a real implementation, this would:
        # 1. Create a Notification record in the database
        # 2. Send via email if 'email' in channels
        # 3. Send via SMS if 'sms' in channels  
        # 4. Send via push if 'push' in channels
        # 5. Store in-app notification
        
        # For now, just log and return success
        return True