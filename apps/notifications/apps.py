"""Notifications app configuration."""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'

    def ready(self):
        # Import signals when all apps are ready to avoid database access warnings
        from django.apps import apps
        if apps.apps_ready:
            import apps.notifications.signals