"""Activity app configuration."""
from django.apps import AppConfig


class ActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.activity'
    verbose_name = 'Activity'

    def ready(self):
        # Connect signals when all apps are ready to avoid database access warnings
        from django.apps import apps
        if apps.apps_ready:
            self._connect_signals()

    def _connect_signals(self):
        """Connect activity logging signals."""
        from django.db.models.signals import post_save, post_delete, pre_save
        from django.dispatch import receiver
        from django.contrib.auth.signals import user_logged_in, user_logged_out

        # Import models and services
        from apps.properties.models import Property, Review, Inquiry, Favorite
        from apps.bookings.models import Booking, Payment
        from kiro.models import UserProfile
        from apps.activity.signals import (
            log_user_login, log_user_logout, log_property_changes, log_property_deletion,
            log_booking_changes, log_payment_changes, log_review_changes,
            log_inquiry_changes, log_favorite_changes, log_profile_updates
        )

        # Connect user authentication signals
        @receiver(user_logged_in)
        def _log_user_login(sender, request, user, **kwargs):
            log_user_login(sender, request, user, **kwargs)

        @receiver(user_logged_out)
        def _log_user_logout(sender, request, user, **kwargs):
            log_user_logout(sender, request, user, **kwargs)

        # Connect property signals
        @receiver(pre_save, sender=Property)
        def _log_property_changes(sender, instance, **kwargs):
            log_property_changes(sender, instance, **kwargs)

        @receiver(post_delete, sender=Property)
        def _log_property_deletion(sender, instance, **kwargs):
            log_property_deletion(sender, instance, **kwargs)

        # Connect booking signals
        @receiver(post_save, sender=Booking)
        def _log_booking_changes(sender, instance, created, **kwargs):
            log_booking_changes(sender, instance, created, **kwargs)

        # Connect payment signals
        @receiver(post_save, sender=Payment)
        def _log_payment_changes(sender, instance, created, **kwargs):
            log_payment_changes(sender, instance, created, **kwargs)

        # Connect review signals
        @receiver(post_save, sender=Review)
        def _log_review_changes(sender, instance, created, **kwargs):
            log_review_changes(sender, instance, created, **kwargs)

        # Connect inquiry signals
        @receiver(post_save, sender=Inquiry)
        def _log_inquiry_changes(sender, instance, created, **kwargs):
            log_inquiry_changes(sender, instance, created, **kwargs)

        # Connect favorite signals
        @receiver(post_save, sender=Favorite)
        def _log_favorite_changes(sender, instance, created, **kwargs):
            log_favorite_changes(sender, instance, created, **kwargs)

        # Connect profile signals
        @receiver(post_save, sender=UserProfile)
        def _log_profile_updates(sender, instance, created, **kwargs):
            log_profile_updates(sender, instance, created, **kwargs)