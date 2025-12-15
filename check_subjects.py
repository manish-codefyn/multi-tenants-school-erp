
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_data():
    from django_tenants.utils import schema_context
    from apps.tenants.models import Tenant
    from apps.academics.models import SchoolClass, ClassSubject
    
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("No tenant found")
            return

        with schema_context(tenant.schema_name):
            print(f"Checking Tenant: {tenant}")
            classes = SchoolClass.objects.filter(is_active=True)
            print(f"Found {classes.count()} active classes.")
            
            for cls in classes:
                subjects = ClassSubject.objects.filter(class_name=cls)
                print(f"Class '{cls.name}' has {subjects.count()} assigned subjects.")
                if subjects.exists():
                    print(f" - Sample: {[s.subject.name for s in subjects[:3]]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_data()
