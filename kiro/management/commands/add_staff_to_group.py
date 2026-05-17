from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from kiro.models import User

class Command(BaseCommand):
    help = 'Add existing staff users to the Staff group'

    def handle(self, *args, **options):
        staff_group, _ = Group.objects.get_or_create(name="Staff")
        staff_users = User.objects.filter(role='staff')
        for user in staff_users:
            if not user.groups.filter(name="Staff").exists():
                user.groups.add(staff_group)
                self.stdout.write(f'Added {user.email} to Staff group')
        self.stdout.write('Done')