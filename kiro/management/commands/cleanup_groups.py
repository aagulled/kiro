"""
Management command to clean up duplicate groups.
"""
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clean up duplicate and unwanted groups"

    def handle(self, *args, **options):
        # Groups to keep
        keep_groups = ["Admin", "Staff", "Host", "Guest", "Agent"]

        # Groups to delete
        delete_groups = ["admin", "agent", "guest", "host", "Moderator", "staff"]

        deleted_count = 0
        for group_name in delete_groups:
            try:
                group = Group.objects.get(name=group_name)
                group.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted group: {group_name}')
                )
                deleted_count += 1
            except Group.DoesNotExist:
                self.stdout.write(
                    f'Group not found: {group_name}'
                )

        self.stdout.write(
            self.style.SUCCESS(f'Cleanup completed. Deleted {deleted_count} groups.')
        )

        # List remaining groups
        remaining = Group.objects.all().values_list('name', flat=True)
        self.stdout.write(f'Remaining groups: {list(remaining)}')