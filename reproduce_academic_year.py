
import os
import django
from django.urls import reverse
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.academics.forms import AcademicYearForm
from apps.users.models import User

def run_test():
    print("Starting Academic Year Reproduction...")
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("No tenant found")
            return

        with schema_context(tenant.schema_name):
            user = User.objects.filter(tenant=tenant).first()
            
            print(f"Testing with Tenant: {tenant}")

            form_data = {
                'name': 'Debug Year 2026',
                'code': 'AY-2026-DEBUG',
                'start_date': '2026-01-01',
                'end_date': '2026-12-31',
                'is_current': False,
                'has_terms': True
            }
            
            print("\n--- Validating Form ---")
            form = AcademicYearForm(data=form_data, tenant=tenant, user=user)
            if form.is_valid():
                print("Form is valid")
            else:
                print("Form Invalid:")
                print(form.errors)

    except Exception as e:
        print(f"Script failed: {e}")

if __name__ == '__main__':
    run_test()
