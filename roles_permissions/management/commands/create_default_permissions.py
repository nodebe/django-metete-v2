from django.core.management.base import BaseCommand
from roles_permissions.services import PermissionService


class Command(BaseCommand):

    def handle(self, *args, **options):
        PermissionService.create_default_permissions()
