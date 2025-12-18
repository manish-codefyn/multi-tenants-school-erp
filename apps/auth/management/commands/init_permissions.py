from django.core.management.base import BaseCommand
from apps.auth.models import RolePermission
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Initialize default role permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant UUID or subdomain to assign permissions for (optional)',
            required=False
        )

    def handle(self, *args, **options):
        self.stdout.write('Initializing permissions...')
        
        tenant_identifier = options.get('tenant')
        
        # If specific tenant requested
        if tenant_identifier:
            try:
                # Try UUID first
                current_tenant = Tenant.objects.filter(id=tenant_identifier).first()
                if not current_tenant:
                    # Try subdomain
                    current_tenant = Tenant.objects.filter(subdomain=tenant_identifier).first()
                
                if current_tenant:
                    self.process_tenant(current_tenant)
                else:
                    self.stdout.write(self.style.ERROR(f'Tenant not found: {tenant_identifier}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error searching tenant: {e}'))
            return

        # Otherwise process all active tenants
        self.stdout.write('Processing all active tenants...')
        from django_tenants.utils import schema_context
        
        tenants = Tenant.objects.filter(is_active=True)
        if not tenants.exists():
             self.stdout.write(self.style.WARNING("No active tenants found."))
             return

        for tenant in tenants:
            self.process_tenant(tenant)

    def process_tenant(self, tenant):
        from django.conf import settings
        
        # Skip public tenant if apps.auth is not in SHARED_APPS
        if tenant.schema_name == getattr(settings, 'PUBLIC_SCHEMA_NAME', 'public'):
             if 'apps.auth' not in settings.SHARED_APPS and 'apps.apps_auth' not in settings.SHARED_APPS:
                self.stdout.write(self.style.WARNING(f'Skipping {tenant.name} (public schema) - apps.auth is not shared'))
                return

        from django_tenants.utils import schema_context
        
        self.stdout.write(f'Processing tenant: {tenant.name} ({tenant.schema_name})')
        try:
            # Switch to tenant schema to access tenant-specific tables (like auth_role_permissions)
            with schema_context(tenant.schema_name):
                # Create permissions 
                count = RolePermission.create_default_permissions(tenant=tenant)
                self.stdout.write(self.style.SUCCESS(f'  - Created/Updated {count} permissions for {tenant.name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  - Error processing {tenant.name}: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
