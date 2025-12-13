import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.students.models import Student
from apps.tenants.models import Tenant
from apps.students.forms import StudentForm

try:
    print("Getting a tenant...")
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant found! Creating one...")
        tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
    
    print(f"Tenant: {tenant} (ID: {tenant.id})")
    
    print("Creating StudentForm...")
    form = StudentForm(data={
        'first_name': 'Test',
        'last_name': 'Student',
        'date_of_birth': '2000-01-01',
        'gender': 'M',
        'personal_email': 'test@example.com',
        'mobile_primary': '+1234567890',
        'admission_type': 'REGULAR',
        # Add minimal required fields...
        'current_class': None, # Optional?
    }, tenant=tenant)
    
    # We don't validate form here because we want to test instance behavior manually first
    # checking instance
    instance = form.instance
    print(f"Instance created. tenant_id: {instance.tenant_id}")
    
    print("Assigning tenant to instance...")
    instance.tenant = tenant
    print(f"Assigned. tenant_id: {instance.tenant_id}")
    
    try:
        print("Accessing instance.tenant...")
        print(f"instance.tenant: {instance.tenant}")
    except Exception as e:
        print(f"Error accessing instance.tenant: {type(e).__name__}: {e}")

    try:
        print("Saving instance (via form behavior logic manually)...")
        # Simulate what CreateView does
        # form_valid -> form.instance.tenant = ... already done
        # form.save() -> instance.save()
        # But form.save() calls instance.save()
        
        # We need to make sure required fields are there for save() to not fail on DB constraints
        # But we are interested in the 'Student has no tenant' error which happens BEFORE DB likely?
        pass # Skipping actual save to DB to avoid pollution unless needed, but the error happens during view execution.
             # The view calls super().form_valid(form) -> form.save() -> instance.save()
        
        # We can try to simulate checking the field descriptor manually
        field = Student._meta.get_field('tenant')
        print(f"Field type: {type(field)}")
        print(f"OneToOne? {field.one_to_one}")
        print(f"ManyToOne? {field.many_to_one}")
    
    except Exception as e:
         print(f"Error: {e}")

except Exception as e:
    print(f"Top level error: {e}")
    import traceback
    traceback.print_exc()
