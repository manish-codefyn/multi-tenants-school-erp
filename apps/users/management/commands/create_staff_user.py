from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context
from apps.users.models import User
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Create a staff user for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('--target-schema', type=str, required=True, help='Schema name of the tenant')
        parser.add_argument('--user-email', type=str, required=True, help='Email of the staff user')
        parser.add_argument('--user-password', type=str, required=True, help='Password for the staff user')
        parser.add_argument('--first-name', type=str, default='Staff', help='First name')
        parser.add_argument('--last-name', type=str, default='User', help='Last name')
        parser.add_argument('--role', type=str, default='staff', help='Role for the staff user')
        parser.add_argument('--is-active', action='store_true', default=True, help='Whether user is active')

    def handle(self, *args, **options):
        schema_name = options['target_schema']
        email = options['user_email']
        password = options['user_password']
        first_name = options['first_name']
        last_name = options['last_name']
        role = options['role']
        is_active = options['is_active']

        try:
            # Check if tenant exists
            if not Tenant.objects.filter(schema_name=schema_name).exists():
                raise CommandError(f"Tenant with schema '{schema_name}' does not exist.")

            # Switch to tenant context
            with schema_context(schema_name):
                tenant = Tenant.objects.get(schema_name=schema_name)
                self.stdout.write(f"Creating staff user for tenant: {tenant.name} ({schema_name})")

                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.WARNING(f"User with email {email} already exists. Updating user."))
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.first_name = first_name
                    user.last_name = last_name
                    user.role = role
                    user.is_active = is_active
                    user.is_staff = True  # Set as staff
                    user.is_superuser = False  # Ensure NOT superuser
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated staff user: {email}"))
                else:
                    # Create new staff user
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        is_active=is_active,
                        is_staff=True,  # Set as staff
                        is_superuser=False,  # Ensure NOT superuser
                        is_verified=True,  # Typically staff users are verified
                        tenant=tenant
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created staff user: {email}"))

        except Exception as e:
            raise CommandError(f"Failed to create staff user: {str(e)}")