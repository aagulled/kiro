"""
Signals for search app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def update_property_search_index(sender, instance, **kwargs):
    """
    Update search index when property is saved.
    """
    from apps.search.models import PropertySearchIndex

    if instance.status == 'active' and not instance.is_deleted:
        search_index, created = PropertySearchIndex.objects.get_or_create(
            property=instance,
            defaults={'is_active': True}
        )
        if not created:
            search_index.update_index()
    else:
        # Deactivate search index for inactive/deleted properties
        PropertySearchIndex.objects.filter(
            property=instance
        ).update(is_active=False)


# Connect signal when apps are ready
from django.apps import apps
if apps.apps_ready:
    from django.db.models.signals import post_save
    from django.dispatch import receiver
    from apps.properties.models import Property

    @receiver(post_save, sender=Property)
    def _update_property_search_index(sender, instance, **kwargs):
        update_property_search_index(sender, instance, **kwargs)