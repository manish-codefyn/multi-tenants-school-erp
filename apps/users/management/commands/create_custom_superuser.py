from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context
from apps.users.models import User
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Create a superuser for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('--target-schema', type=str, required=True, help='Schema name of the tenant')
        parser.add_argument('--user-email', type=str, required=True, help='Email of the superuser')
        parser.add_argument('--user-password', type=str, required=True, help='Password for the superuser')
        parser.add_argument('--first_name', type=str, default='Super', help='First name')
        parser.add_argument('--last_name', type=str, default='Admin', help='Last name')

    def handle(self, *args, **options):
        schema_name = options['target_schema']
        email = options['user_email']
        password = options['user_password']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            # Check if tenant exists
            if not Tenant.objects.filter(schema_name=schema_name).exists():
                raise CommandError(f"Tenant with schema '{schema_name}' does not exist.")

            # Switch to tenant context
            with schema_context(schema_name):
                tenant = Tenant.objects.get(schema_name=schema_name)
                self.stdout.write(f"Creating superuser for tenant: {tenant.name} ({schema_name})")

                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.WARNING(f"User with email {email} already exists. Updating password."))
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.is_superuser = True
                    user.is_staff = True
                    user.role = 'super_admin'
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated superuser: {email}"))
                else:
                    # Create new superuser
                    User.objects.create_superuser(
                        email=email,
                        password=password,
                        tenant=tenant,
                        first_name=first_name,
                        last_name=last_name,
                        role='super_admin',
                        is_verified=True
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created superuser: {email}"))

        except Exception as e:
            raise CommandError(f"Failed to create superuser: {str(e)}")
