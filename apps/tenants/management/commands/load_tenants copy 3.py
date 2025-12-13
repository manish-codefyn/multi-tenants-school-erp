import json
import os
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from django_tenants.utils import schema_context
from django.utils.text import slugify
from apps.tenants.models import Tenant, Domain

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
        
        for data in tenants_data:
            try:
                # Always use public schema context for tenant creation/update
                with schema_context('public'):
                    schema_name = data.get('schema_name')
                    domain_name = data.pop('domain')
                    
                    # Generate slug from name if not provided in JSON
                    if 'slug' not in data:
                        data['slug'] = slugify(data.get('name', ''))
                    
                    # Check if tenant exists
                    tenant = Tenant.objects.filter(schema_name=schema_name).first()
                    
                    if tenant:
                        self.stdout.write(f"Updating existing tenant: {schema_name}")
                        
                        # Update existing tenant fields
                        Tenant.objects.filter(pk=tenant.pk).update(**data)
                        
                        # Update domain if needed
                        Domain.objects.filter(tenant=tenant, is_primary=True).update(domain=domain_name)
                        
                        self.stdout.write(self.style.SUCCESS(f"Updated tenant: {data['name']}"))
                        updated_count += 1
                        
                    else:
                        self.stdout.write(f"Creating new tenant: {schema_name}")
                        
                        # Generate UUID for new tenant
                        tenant_id = uuid.uuid4()
                        
                        # Ensure slug is set
                        if not data.get('slug'):
                            data['slug'] = slugify(data.get('name', ''))
                        
                        # Check if slug already exists
                        existing_slug = Tenant.objects.filter(slug=data['slug']).exists()
                        if existing_slug:
                            # Add schema_name to make slug unique
                            data['slug'] = f"{data['slug']}-{schema_name}"
                        
                        # Create tenant instance
                        tenant = Tenant(
                            id=tenant_id,
                            tenant_id=tenant_id,  # Self-reference
                            **data
                        )
                        
                        # Use save() to trigger validation and schema creation
                        tenant.save()
                        
                        # Create domain
                        domain = Domain(
                            domain=domain_name,
                            tenant=tenant,
                            is_primary=True
                        )
                        domain.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"Created tenant: {data['name']} with domain: {domain_name}"))
                        created_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process {data.get('schema_name', 'unknown')}: {str(e)}"))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        # Display detailed results
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TENANT DATABASE REPORT")
        self.stdout.write("="*80)
        self.stdout.write(f"Total Created: {created_count}")
        self.stdout.write(f"Total Updated: {updated_count}")
        
        with schema_context('public'):
            tenants = Tenant.objects.all().order_by('schema_name')
            self.stdout.write(f"Total Tenants: {tenants.count()}")
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'Schema':<20} | {'Name':<30} | {'Domain':<25} | {'Status':<10}")
            self.stdout.write("-" * 80)
            
            for tenant in tenants:
                # Get primary domain
                domain = Domain.objects.filter(tenant=tenant, is_primary=True).first()
                domain_name = domain.domain if domain else "No Domain"
                
                self.stdout.write(f"{tenant.schema_name:<20} | {tenant.name[:28]:<30} | {domain_name:<25} | {tenant.status:<10}")
            
            self.stdout.write("-" * 80)