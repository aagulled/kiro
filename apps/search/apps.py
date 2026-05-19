"""Search app configuration."""
from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    verbose_name = 'Search'

    def ready(self):
        # Import signals when all apps are ready to avoid database access warnings
        from django.apps import apps
        if apps.apps_ready:
            import apps.search.signals