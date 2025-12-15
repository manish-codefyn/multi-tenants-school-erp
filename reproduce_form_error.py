
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.tenants.models import Tenant, Domain
from apps.academics.forms import TermForm
from apps.academics.models import AcademicYear

def run_test():
    print("Starting reproduction test...")
    
    # 1. Create/Get Tenant
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            tenant, created = Tenant.objects.get_or_create(
                schema_name='test',
                defaults={'name': 'Test Tenant'}
            )
        print(f"Tenant: {tenant} (ID: {tenant.id})")
    except Exception as e:
        print(f"Error getting/creating tenant: {e}")
        return
    
    # 2. Create User
    try:
        user, created = User.objects.get_or_create(
            email='testuser@example.com',
            username='testuser',
            defaults={'tenant': tenant}
        )
        print(f"User: {user}")
    except Exception as e:
        print(f"Error getting/creating user: {e}")
        return
    
    # 3. Create Academic Year (required for Term)
    # We need to manually set tenant because we are not using the form here
    try:
        academic_year, created = AcademicYear.objects.get_or_create(
            code='AY-2025-TEST',
            tenant=tenant,
            defaults={
                'name': 'Test Year 2025',
                'start_date': '2025-01-01',
                'end_date': '2025-12-31',
                'is_current': True
            }
        )
        print(f"Academic Year: {academic_year} (Tenant: {academic_year.tenant_id})")
    except Exception as e:
        print(f"Error getting/creating AcademicYear: {e}")
        return

    # 4. Form Data
    form_data = {
        'academic_year': academic_year.id,
        'name': 'Term 1',
        'term_type': 'FIRST_TERM',
        'order': 1,
        'start_date': '2025-01-01',
        'end_date': '2025-03-31',
        'is_current': True
    }
    
    # 5. Initialize Form with tenant
    print("\n--- Initializing Form with tenant ---")
    # Simulate BaseCreateView behavior: passing request isn't easy here, so we rely on 'tenant' kwarg
    form = TermForm(data=form_data, tenant=tenant, user=user)
    
    # 6. Validate
    print("Calling form.is_valid()...")
    is_valid = form.is_valid()
    print(f"Is Valid: {is_valid}")
    
    if not is_valid:
        print(f"Errors: {form.errors}")
    else:
        print("Form is valid.")
        instance = form.save(commit=False)
        print(f"Instance Tenant: {instance.tenant_id}")
        
    # Check if we can save
    if is_valid:
        try:
            instance.save()
            print("Successfully saved instance.")
        except Exception as e:
            print(f"Save failed: {e}")
            
if __name__ == '__main__':
    run_test()
