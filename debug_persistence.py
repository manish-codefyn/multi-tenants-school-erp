
import os
import django
import sys
from django.core.exceptions import ValidationError

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.tenants.models import Tenant
from apps.core.utils.tenant import set_current_tenant, clear_tenant

def debug_persistence():
    print("Debugging User Persistence...")
    clear_tenant()
    
    # 1. Setup Tenant and User
    print("\n1. Setting up Test Data...")
    
    tenant = Tenant.objects.first()
    if tenant:
        print(f"Using existing Tenant: {tenant.name} ({tenant.pk})")
    else:
        print("Creating new Tenant...")
        tenant = Tenant.objects.create(
            name='Debug Tenant', 
            schema_name='debug_tenant',
            display_name='Debug Tenant', 
            status='active'
        )
    
    set_current_tenant(tenant)
    
    user = User.objects.filter(email='debug_persistence@example.com').first()
    if not user:
        # Try to use any existing user if the specific debug user doesn't exist
        user = User.objects.filter(tenant=tenant).first()
        if user:
             print(f"Using existing user from DB: {user.email}")
        else:
            print("Creating debug user...")
            user = User.objects.create_user(
                email='debug_persistence@example.com',
                password='password',
                tenant=tenant,
                role='student',
                first_name='Debug',
                last_name='User'
            )
    
    print(f"User: {user.email} (Role: {user.role}, Is Staff: {user.is_staff})")
    
    # 2. Test Role Change
    print("\n2. Testing Role Change...")
    old_role = user.role
    new_role = 'teacher'
    user.role = new_role
    print(f"Set role to: {new_role}")
    
    try:
        print("Attempting validation (full_clean)...")
        user.full_clean()
        print("Validation passed.")
        
        print("Attempting save()...")
        user.save()
        print("Save successful.")
        
        user.refresh_from_db()
        print(f"Reloaded Role: {user.role}")
        
        if user.role == new_role:
            print("[SUCCESS] Role persisted.")
        else:
            print("[FAILURE] Role did NOT persist.")
            
    except ValidationError as e:
        print(f"[ERROR] Validation Error: {e}")
    except Exception as e:
        print(f"[ERROR] Exception during save: {e}")
        import traceback
        traceback.print_exc()

    # 3. Test Staff Toggle
    print("\n3. Testing Staff Toggle...")
    user.is_staff = not user.is_staff
    print(f"Set is_staff to: {user.is_staff}")
    
    try:
        print("Attempting validation (full_clean)...")
        user.full_clean()
        print("Validation passed.")
        
        print("Attempting save()...")
        user.save()
        print("Save successful.")
        
        user.refresh_from_db()
        print(f"Reloaded is_staff: {user.is_staff}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

    # Cleanup
    print("\nCleaning up...")
    # Only delete if it's the specific debug user
    if user.email == 'debug_persistence@example.com':
        user.delete()
        print("Debug user deleted.")
    else:
        print("Skipping user deletion (using existing user).")
        
    # Don't delete tenant as we might be using a real one

if __name__ == '__main__':
    debug_persistence()
