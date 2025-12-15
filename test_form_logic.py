
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.tenants.models import Tenant
from apps.academics.forms import TermForm
from apps.academics.models import AcademicYear

from django_tenants.utils import schema_context

def run_test():
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("No tenant found")
            sys.exit(1)
            
        with schema_context(tenant.schema_name):
            user = User.objects.filter(tenant=tenant).first()
            
            academic_year = AcademicYear.objects.filter(tenant=tenant).first()
            if not academic_year:
                academic_year = AcademicYear.objects.create(
                    tenant=tenant, 
                    name="Test Year", 
                    code="TY2025", 
                    start_date="2025-01-01", 
                    end_date="2025-12-31"
                )

            form_data = {
                'academic_year': academic_year.id,
                'name': 'Test Term Validation',
                'term_type': 'FIRST_TERM',
                'order': 1,
                'start_date': '2025-01-01',
                'end_date': '2025-03-31',
                'is_current': True
            }
            
            print("Initializing form...")
            # Simulate request logic by creating form with tenant
            form = TermForm(data=form_data, tenant=tenant, user=user)
            
            if not form.is_valid():
                print("Layout error: Form is invalid!")
                print(form.errors)
                if '__all__' in form.errors:
                    print("Global errors found.")
                sys.exit(1)
                
            print("Form is valid! Tenant assignment worked.")
            sys.exit(0)

    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_test()
