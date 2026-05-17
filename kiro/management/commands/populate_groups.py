"""
Management command to populate default groups.
"""
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Populate default groups"

    def handle(self, *args, **options):
        groups = [
            "Host",
            "Guest",
            "Agent",
            "Staff",
            "Admin",
        ]

        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group.name}')
                )
            else:
                self.stdout.write(
                    f'Group already exists: {group.name}'
                )

        self.stdout.write(
            self.style.SUCCESS('Groups population completed.')
        )