import time
from django.core.management.base import BaseCommand
from accounts.models import ServiceProvider
from accounts.views import geocode_city

class Command(BaseCommand):
    help = 'Geocodes existing service providers who have no coordinates'

    def handle(self, *args, **options):
        # Only target providers missing coordinates
        providers = ServiceProvider.objects.filter(latitude__isnull=True)
        total = providers.count()
        success_count = 0
        fail_count = 0

        self.stdout.write(self.style.NOTICE(f"Starting geocoding for {total} providers..."))

        for provider in providers:
            lat, lng = geocode_city(provider.location)
            
            if lat and lng:
                provider.latitude = lat
                provider.longitude = lng
                provider.save()
                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Geocoded: {provider.location} → {lat:.4f}, {lng:.4f}"
                ))
            else:
                fail_count += 1
                self.stdout.write(self.style.WARNING(
                    f"Could not geocode: [{provider.location}]"
                ))

            # Respect Nominatim Usage Policy (Max 1 request per second)
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(
            f"Done. {success_count} providers geocoded, {fail_count} failed."
        ))