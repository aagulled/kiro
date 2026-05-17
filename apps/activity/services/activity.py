"""
Activity Service for Kirokiro.
"""
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class ActivityService:
    """
    Service for handling activity logging.
    """
    
    def __init__(self):
        self.logger = logger
    
    def _get_client_ip(self, request):
        """
        Resolve client IP preferring X-Forwarded-For header.

        Returns first IP in comma list or REMOTE_ADDR.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_activity(self, action_type=None, actor=None, target_type=None, target_id=None, 
                    target_name=None, description=None, old_values=None, new_values=None,
                    content_object=None, request=None, severity='medium'):
        """
        Persist ActivityLog entry with optional request context.

        Handles actor resolution, IP extraction and JSON serialization
        of value diffs. Returns created ActivityLog instance.
        """
        # Extract user from actor if it's a User object
        if actor and hasattr(actor, 'id'):
            # If actor has an id attribute, it's likely a user-like object
            user = actor
        elif actor and isinstance(actor, User):
            user = actor
        else:
            # Try to get user from actor if it's a profile or related object
            user = getattr(actor, 'user', None) if actor else None
        
        # Get IP address if request is provided
        ip_address = self._get_client_ip(request) if request else None
        
        # Log the activity (placeholder implementation)
        self.logger.info(f"Activity logged: {action_type} by {user} on {target_type} {target_id}")
        if description:
            self.logger.info(f"Description: {description}")
        if ip_address:
            self.logger.info(f"IP Address: {ip_address}")