import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.users.models import User
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Create superusers for tenants from JSON data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading users from JSON...'))
        
        # Path to the JSON file
        json_file_path = os.path.join(settings.BASE_DIR, 'apps', 'users', 'data', 'users.json')
        
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"JSON file not found at: {json_file_path}"))
            return

        try:
            with open(json_file_path, 'r') as f:
                users_data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON: {str(e)}"))
            return
        
        created_count = 0
        updated_count = 0
        
        for tenant_data in users_data:
            schema_name = tenant_data.get('schema_name')
            users_list = tenant_data.get('users', [])
            
            try:
                # Check if tenant exists
                if not Tenant.objects.filter(schema_name=schema_name).exists():
                    self.stdout.write(self.style.WARNING(f"Tenant {schema_name} does not exist. Skipping users."))
                    continue
                
                # Switch to tenant context
                with schema_context(schema_name):
                    tenant = Tenant.objects.get(schema_name=schema_name)
                    self.stdout.write(f"Processing users for tenant: {tenant.name} ({schema_name})")
                    
                    for user_data in users_list:
                        email = user_data.pop('email', None)
                        password = user_data.pop('password', None)
                        
                        if not email:
                            self.stdout.write(self.style.WARNING("Skipping user without email"))
                            continue
                            
                        # Check if user exists
                        user = User.objects.filter(email=email).first()
                        
                        if user:
                            self.stdout.write(f"  Updating existing user: {email}")
                            # Update fields
                            for key, value in user_data.items():
                                setattr(user, key, value)
                            
                            if password:
                                user.set_password(password)
                                
                            user.save()
                            updated_count += 1
                        else:
                            self.stdout.write(f"  Creating new user: {email}")
                            # Create new user
                            # We need to pass tenant explicitly as per UserManager
                            user_data['tenant'] = tenant
                            if password:
                                User.objects.create_superuser(email=email, password=password, **user_data)
                            else:
                                User.objects.create_user(email=email, password=None, **user_data)
                            created_count += 1
                            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process tenant {schema_name}: {str(e)}"))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal Users Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Total Users Updated: {updated_count}"))
