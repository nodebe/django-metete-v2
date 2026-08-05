from django.core.management.base import BaseCommand
from roles_permissions.services import RoleService


class Command(BaseCommand):

    def handle(self, *args, **options):
        RoleService.create_default_roles()
