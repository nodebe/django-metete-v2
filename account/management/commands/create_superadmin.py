from django.conf import settings
from django.core.management.base import BaseCommand
from account.models import User
from base.management.commands.seed_defaults import create_mailsender
from utils.service import generate_random_username, get_unique_id


# Create default Superadmin - make sure to set the ADMIN_PASSWORD & ADMIN_EMAIL in env
# python manage.py create_superadmin --first_admin=True

# Create super admin
# python manage.py create_superadmin --email=admin@email.com --password=Default@123 --username=admin_name


class Command(BaseCommand):
    help = 'Create Superadmin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of admin',
            default=generate_random_username()
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of admin'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password of account'
        )
        parser.add_argument(
            '--phone_number',
            type=str,
            help='Phone number of admin'
        )
        parser.add_argument(
            '--first_admin',
            type=str,
            help='First admin username'
        )

    def handle(self, *args, **options):
        create_mailsender()
        first_admin = options['first_admin']

        if first_admin:
            username = generate_random_username()
            email = settings.ADMIN_EMAIL
            password = settings.ADMIN_PASSWORD
            phone_number = settings.ADMIN_PHONE_NUMBER

        else:
            username = options['username']
            email = options['email']
            password = options['password']
            phone_number = options["phone_number"]

        if not email or not password:
            self.stdout.write(self.style.ERROR(f"Email and Password are required."))
            return

        try:
            _ = User.objects.create_superuser(
                user_id=get_unique_id(length=10),
                username=username,
                phone_number=phone_number,
                email=email,
                password=password
            )

            self.stdout.write(self.style.SUCCESS(f"Admin account created for: {username}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{e}"))
