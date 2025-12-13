import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context, get_tenant_model
from django.utils.text import slugify
from apps.tenants.models import Tenant, Domain
from django.db import connection

class Command(BaseCommand):
    help = 'Manually create or update tenants from JSON data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading tenants from JSON...'))
        
        # Path to the JSON file
        json_file_path = os.path.join(settings.BASE_DIR, 'apps', 'tenants', 'data', 'tenants.json')
        
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"JSON file not found at: {json_file_path}"))
            return

        try:
            with open(json_file_path, 'r') as f:
                tenants_data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {str(e)}"))
            return
        
        created_count = 0
        updated_count = 0
        
        # Process public tenant first if it exists in JSON
        public_data = None
        other_tenants = []
        
        for data in tenants_data:
            if data.get('schema_name') == 'public':
                public_data = data
            else:
                other_tenants.append(data)
        
        # Process public tenant first
        if public_data:
            try:
                self.process_tenant(public_data, is_public=True)
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process public: {str(e)}"))
        
        # Process other tenants
        for data in other_tenants:
            try:
                self.process_tenant(data, is_public=False)
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process {data.get('schema_name', 'unknown')}: {str(e)}"))
        
        # Display report
        self.display_report()
    
    def process_tenant(self, data, is_public=False):
        """Process a single tenant creation/update"""
        schema_name = data.get('schema_name')
        domain_name = data.pop('domain')
        
        # Remove tenant_id if present
        data.pop('tenant_id', None)
        
        # Generate slug from name if not provided
        if 'slug' not in data:
            data['slug'] = slugify(data.get('name', ''))
        
        with schema_context('public'):
            # Check if tenant exists
            tenant = Tenant.objects.filter(schema_name=schema_name).first()
            
            if tenant:
                self.stdout.write(f"Updating existing tenant: {schema_name}")
                
                # Update existing tenant fields
                for key, value in data.items():
                    setattr(tenant, key, value)
                tenant.save()
                
                # Update domain if needed
                domain = Domain.objects.filter(tenant=tenant, is_primary=True).first()
                if domain:
                    if domain.domain != domain_name:
                        domain.domain = domain_name
                        domain.save()
                else:
                    domain = Domain(
                        domain=domain_name,
                        tenant=tenant,
                        is_primary=True
                    )
                    domain.save()
                
                self.stdout.write(self.style.SUCCESS(f"Updated tenant: {data['name']}"))
                return tenant
                
            else:
                self.stdout.write(f"Creating new tenant: {schema_name}")
                
                # Ensure slug is set
                if not data.get('slug'):
                    data['slug'] = slugify(data.get('name', ''))
                
                # Check if slug already exists
                existing_slug = Tenant.objects.filter(slug=data['slug']).exists()
                if existing_slug:
                    data['slug'] = f"{data['slug']}-{schema_name}"
                
                # Set schema_name explicitly
                data['schema_name'] = schema_name
                
                # Create tenant instance
                tenant = Tenant(**data)
                
                # For public tenant, we need to ensure migrations are run first
                if is_public:
                    # Save tenant first
                    tenant.save()
                    
                    # Create domain
                    domain = Domain(
                        domain=domain_name,
                        tenant=tenant,
                        is_primary=True
                    )
                    domain.save()
                    
                    # Run migrations for public schema
                    self.stdout.write(f"Running migrations for public schema...")
                    from django.core.management import call_command
                    call_command('migrate', '--schema=public')
                    
                else:
                    # For regular tenants, save will trigger schema creation
                    tenant.save()
                    
                    # Create domain
                    domain = Domain(
                        domain=domain_name,
                        tenant=tenant,
                        is_primary=True
                    )
                    domain.save()
                    
                    # Run migrations for the tenant schema
                    self.stdout.write(f"Running migrations for {schema_name} schema...")
                    from django.core.management import call_command
                    call_command('migrate', f'--schema={schema_name}')
                
                self.stdout.write(self.style.SUCCESS(f"Created tenant: {data['name']} with domain: {domain_name}"))
                return tenant
    
    def display_report(self):
        """Display a report of all tenants"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TENANT DATABASE REPORT")
        self.stdout.write("="*80)
        
        with schema_context('public'):
            tenants = Tenant.objects.all().order_by('schema_name')
            self.stdout.write(f"Total Tenants: {tenants.count()}")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'Schema':<20} | {'Name':<30} | {'Domain':<25} | {'Status':<10}")
            self.stdout.write("-" * 80)
            
            for tenant in tenants:
                domain = Domain.objects.filter(tenant=tenant, is_primary=True).first()
                domain_name = domain.domain if domain else "No Domain"
                
                self.stdout.write(f"{tenant.schema_name:<20} | {tenant.name[:28]:<30} | {domain_name:<25} | {tenant.status:<10}")
            
            self.stdout.write("-" * 80)