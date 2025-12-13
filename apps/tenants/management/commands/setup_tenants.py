from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = 'Complete system setup: migrations, tenants, and initial data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Complete System Setup...'))
        self.stdout.write('=' * 50)

        # 1. Run Migrations (Public only)
        self.stdout.write('\nStep 1: Running Migrations (Public)...')
        try:
            # Migrate public schema first
            self.stdout.write('   Migrating public schema...')
            call_command('migrate_schemas', schema='public')
            self.stdout.write(self.style.SUCCESS('   Public schema migrated successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error running public migrations: {str(e)}'))
            return

        # 2. Load Tenants
        self.stdout.write('\nStep 2: Loading Tenants...')
        try:
            call_command('load_tenants')
            self.stdout.write(self.style.SUCCESS('   Tenants loaded successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error loading tenants: {str(e)}'))
            # Continue even if tenant loading fails

        # 2.5 Verify/Create Schemas
        self.stdout.write('\nStep 2.5: Verifying Schemas...')
        try:
            from apps.tenants.models import Tenant
            from django_tenants.utils import schema_exists
            
            for tenant in Tenant.objects.all():
                if not schema_exists(tenant.schema_name):
                    self.stdout.write(f"   Creating missing schema for {tenant.schema_name}...")
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{tenant.schema_name}"')
                        self.stdout.write(self.style.SUCCESS(f"   Created schema: {tenant.schema_name}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   Failed to create schema {tenant.schema_name}: {e}"))
        except Exception as e:
             self.stdout.write(self.style.ERROR(f"   Error verifying schemas: {e}"))

        # 3. Run Migrations (All Tenants)
        self.stdout.write('\nStep 3: Running Migrations (All Tenants)...')
        try:
            # Migrate all schemas
            self.stdout.write('   Migrating all schemas...')
            call_command('migrate_schemas')
            self.stdout.write(self.style.SUCCESS('   All schemas migrated successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error running migrations: {str(e)}'))
            return

        # 3. Load Core Initial Data
        self.stdout.write('\nStep 3: Loading Core Initial Data...')
        try:
            call_command('load_core_initial')
            self.stdout.write(self.style.SUCCESS('   Core data loaded successfully'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Error loading core data (might be optional): {str(e)}'))

        # 4. Load Users Initial Data
        self.stdout.write('\nStep 4: Loading Users Initial Data...')
        try:
            call_command('load_users_initial')
            self.stdout.write(self.style.SUCCESS('   User data loaded successfully'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Error loading user data (might be optional): {str(e)}'))

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('System Setup Complete!'))
