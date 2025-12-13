
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django_tenants.utils import schema_context
from apps.students.models import Student
from apps.tenants.models import Tenant

def check_students():
    tenants = Tenant.objects.all()
    print(f"Found {tenants.count()} tenants:")
    for t in tenants:
        print(f" - {t.name} (Schema: {t.schema_name})")
        
        if t.schema_name != 'public':
            with schema_context(t.schema_name):
                count = Student.objects.all().count()
                print(f"   Students: {count}")
                if count > 0:
                   recent = Student.objects.order_by('-created_at')[:3]
                   for s in recent:
                       print(f"   - {s.full_name} ({s.personal_email})")

if __name__ == "__main__":
    check_students()
