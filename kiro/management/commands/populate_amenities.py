"""
Management command to populate default amenities.
"""
from django.core.management.base import BaseCommand

from kiro.models import Amenity


class Command(BaseCommand):
    help = "Populate default amenities"

    def handle(self, *args, **options):
        amenities = [
            {"name": "WiFi", "category": "Connectivity"},
            {"name": "Parking", "category": "Transportation"},
            {"name": "Heating", "category": "Comfort"},
            {"name": "Cooling", "category": "Comfort"},
            {"name": "Electricity", "category": "Utilities"},
            {"name": "Water", "category": "Utilities"},
            {"name": "Elevator", "category": "Accessibility"},
            {"name": "Security", "category": "Safety"},
            {"name": "Furnished", "category": "Furnishings"},
            {"name": "Balcony", "category": "Outdoor"},
            {"name": "Garden", "category": "Outdoor"},
            {"name": "Terrace", "category": "Outdoor"},
            {"name": "Kitchen", "category": "Appliances"},
            {"name": "Laundry", "category": "Appliances"},
            {"name": "Workspace", "category": "Work"},
            {"name": "Fireplace", "category": "Comfort"},
        ]

        for amenity_data in amenities:
            amenity, created = Amenity.objects.get_or_create(
                name=amenity_data["name"],
                defaults={"category": amenity_data["category"]},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created amenity: {amenity.name}')
                )
            else:
                self.stdout.write(
                    f'Amenity already exists: {amenity.name}'
                )

        self.stdout.write(
            self.style.SUCCESS('Amenities population completed.')
        )