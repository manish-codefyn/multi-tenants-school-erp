import uuid
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain

class Command(BaseCommand):
    help = 'Manually create tenants for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating tenants manually...'))
        
        tenants_data = [
            {
                'schema_name': 'public',
                'name': 'System Tenant',
                'display_name': 'System Management',
                'contact_email': 'admin@system.com',
                'max_users': 100,
                'max_storage_mb': 10240,
                'domain': 'localhost'
            },
            {
                'schema_name': 'university_a',
                'name': 'University A',
                'display_name': 'University A Campus',
                'contact_email': 'admin@university-a.edu',
                'max_users': 500,
                'max_storage_mb': 5120,
                'domain': 'university-a.localhost'
            }
        ]
        
        created_count = 0
        
        for data in tenants_data:
            try:
                # Always use public schema context for tenant creation
                with schema_context('public'):
                    # Check if tenant exists
                    if Tenant.objects.filter(schema_name=data['schema_name']).exists():
                        self.stdout.write(self.style.WARNING(f"Tenant {data['schema_name']} already exists"))
                        continue
                    
                    # Generate UUID for new tenant
                    tenant_id = uuid.uuid4()
                    
                    # Create tenant instance with self-referencing tenant_id
                    # We use bulk_create to bypass the save() method which enforces tenant context
                    tenant = Tenant(
                        id=tenant_id,
                        tenant_id=tenant_id,  # Self-reference
                        schema_name=data['schema_name'],
                        name=data['name'],
                        display_name=data['display_name'],
                        contact_email=data['contact_email'],
                        max_users=data['max_users'],
                        max_storage_mb=data['max_storage_mb'],
                        is_active=True
                    )
                    
                    # Use bulk_create to skip custom save() validation
                    Tenant.objects.bulk_create([tenant])
                    
                    # Fetch the created tenant to ensure we have a fresh instance
                    tenant = Tenant.objects.get(id=tenant_id)
                    
                    # Manually trigger post_save signal to create schema
                    # django-tenants uses this signal to create the schema
                    post_save.send(
                        sender=Tenant,
                        instance=tenant,
                        created=True,
                        using='default',
                        update_fields=None
                    )
                    
                    # Create domain
                    domain = Domain(
                        domain=data['domain'],
                        tenant=tenant,
                        is_primary=True
                    )
                    Domain.objects.bulk_create([domain])
                    
                    self.stdout.write(self.style.SUCCESS(f"Created tenant: {data['name']} with domain: {data['domain']}"))
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create {data['schema_name']}: {str(e)}"))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        # Display results
        with schema_context('public'):
            tenants = Tenant.objects.all()
            self.stdout.write(self.style.SUCCESS(f"\nTotal tenants created: {created_count}"))
            self.stdout.write(self.style.SUCCESS(f"Total tenants in database: {tenants.count()}"))
            for tenant in tenants:
                self.stdout.write(f" - {tenant.name} ({tenant.schema_name})")