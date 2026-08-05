from django.core.management.base import BaseCommand

from location.v1.services import LocationService


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--country', required=False)

    def handle(self, *args, **options):
        """
            Populate cities of all countries by default
            Populate cities of a particular country by passing in the country name as an arg
            e.g. python manage.py seed_cities --country Nigeria
        """
        country = options.get("country")
        location_service = LocationService(None)

        location_service.create_cities(country=country)
