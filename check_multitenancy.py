import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.users.models import User

def verify_multitenancy():
    print("Verifying Multi-Tenant Setup...")
    
    # 1. Create Tenant
    tenant_name = "Test School"
    schema_name = "test_school"
    
    if Tenant.objects.filter(schema_name=schema_name).exists():
        print(f"Tenant {schema_name} already exists. Cleaning up...")
        Tenant.objects.filter(schema_name=schema_name).delete()
        
    print(f"Creating Tenant: {tenant_name} ({schema_name})")
    tenant = Tenant(
        name=tenant_name,
        schema_name=schema_name
    )
    tenant.save()
    
    # 2. Create Domain
    domain_url = "testschool.localhost"
    print(f"Creating Domain: {domain_url}")
    domain = Domain(
        domain=domain_url,
        tenant=tenant,
        is_primary=True
    )
    domain.save()
    
    # 3. Create Tenant User
    print("Creating Tenant User...")
    with schema_context(schema_name):
        if not User.objects.filter(email="admin@testschool.com").exists():
            user = User.objects.create_user(
                email="admin@testschool.com",
                password="password123",
                tenant=tenant,
                role=User.ROLE_ADMIN
            )
            print(f"User created: {user.email} in schema {schema_name}")
        else:
            print("User already exists")
            
    # 4. Verify Isolation
    print("Verifying Isolation...")
    
    public_users = User.objects.filter(tenant=tenant)
    print(f"Users found in public query for tenant: {public_users.count()}")
    
    print("Verification Complete. Tenant created successfully.")

if __name__ == "__main__":
    verify_multitenancy()
