import json
import os

from django.core.management.base import BaseCommand
from media.models import Media


class Command(BaseCommand):
    help = "Seed or update media types from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='media_types.json',
            help="Path to the JSON file containing media type definitions"
        )

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), 'data', 'media_types.json')

        # Load JSON
        with open(file_path, 'r') as f:
            media_types = json.load(f)

        created_count = 0
        updated_count = 0

        for item in media_types:
            media_obj, created = Media.objects.update_or_create(
                label=item["label"],
                defaults={
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "allowed_file_types": item.get("allowed_file_types", []),
                    "max_file_size_in_kb": item.get("max_file_size_in_kb", 1000),
                    "upload_to": item.get("upload_to"),
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Media seed complete: {created_count} created, {updated_count} updated."
            )
        )
