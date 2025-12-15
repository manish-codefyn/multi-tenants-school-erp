import os
import django
import sys
sys.path.append(os.getcwd())

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django_tenants.utils import tenant_context

from apps.tenants.models import Tenant
from apps.students.models import Student

def find_student():
    print("Searching for student VEDA DHAR...")
    tenants = Tenant.objects.exclude(schema_name='public')
    
    found = False
    for t in tenants:
        try:
            with tenant_context(t):
                s = Student.objects.filter(first_name__icontains='VEDA').first()
                if s:
                    print(f"FOUND in tenant: {t.schema_name}")
                    print(f"  Name: {s.full_name}")
                    print(f"  Admission No: '{s.admission_number}'")
                    print(f"  Reg No: '{s.reg_no}'")
                    print(f"  Status: {s.status}")
                    found = True
        except Exception as e:
            print(f"Error checking tenant {t.schema_name}: {e}")

    if not found:
        print("Student not found in any tenant.")

if __name__ == "__main__":
    find_student()
