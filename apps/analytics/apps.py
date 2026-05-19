"""Analytics app configuration for metrics and reporting."""
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = 'Analytics'

    def ready(self):
        # Import signals when all apps are ready to avoid database access warnings
        from django.apps import apps
        if apps.apps_ready:
            import apps.analytics.signals