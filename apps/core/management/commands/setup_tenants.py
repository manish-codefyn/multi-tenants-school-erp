# apps/core/management/commands/setup_tenants.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Setup initial tenants'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-default',
            action='store_true',
            help='Create default tenant',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up tenants...')
        
        from apps.tenants.models import Tenant
        
        # Create default tenant if requested
        if options['create_default']:
            default_tenant, created = Tenant.objects.get_or_create(
                name='Default School',
                schema_name='public',
                defaults={
                    'description': 'Default school tenant',
                    'domain_url': 'localhost',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('  ✓ Created default tenant'))
            else:
                self.stdout.write('  ⚡ Default tenant already exists')
        
        # List existing tenants
        tenants = Tenant.objects.all()
        self.stdout.write(f'\nFound {tenants.count()} tenant(s):')
        
        for tenant in tenants:
            status = '✓ Active' if tenant.is_active else '✗ Inactive'
            self.stdout.write(f'  {status} {tenant.name} ({tenant.schema_name})')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Tenant setup complete!'))