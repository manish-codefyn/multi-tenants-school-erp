
import os
import django
import sys
from datetime import date

# Add project root to path
sys.path.append('H:/works/python/Multi-Tenant/EduERP_by_AI')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.academics.models import AcademicYear, SchoolClass, Section, Stream
from apps.users.models import User

def setup():
    try:
        tenant = Tenant.objects.get(schema_name='dpskolkata')
    except Tenant.DoesNotExist:
        # Create tenant if it doesn't exist (unlikely given previous logs, but safe)
        print("Tenant 'dpskolkata' not found. Creating...")
        tenant = Tenant.objects.create(
            schema_name='dpskolkata',
            name='DPS Kolkata',
            display_name='Delhi Public School, Kolkata',
            plan='enterprise',
            is_active=True
        )
        # Assuming domain creation happens automatically or is not strictly needed for this script context if we use schema_context
    
    print(f"Using tenant: {tenant}")

    with schema_context(tenant.schema_name):
        # 1. Create Academic Year
        year, created = AcademicYear.objects.get_or_create(
            code='2025-26',
            defaults={
                'name': '2025-2026',
                'start_date': date(2025, 4, 1),
                'end_date': date(2026, 3, 31),
                'is_current': True
            }
        )
        print(f"Academic Year: {year} (Created: {created})")

        # 2. Create Class
        cls, created = SchoolClass.objects.get_or_create(
            code='10',
            defaults={
                'name': 'Class 10',
                'numeric_name': 10,
                'level': 'HIGH',
                'order': 10,
                'is_active': True
            }
        )
        print(f"Class: {cls} (Created: {created})")

        # 3. Create Section
        section, created = Section.objects.get_or_create(
            class_name=cls,
            name='A',
            defaults={
                'code': '10A',
                'room_number': '101',
                'is_active': True
            }
        )
        print(f"Section: {section} (Created: {created})")
        
        # 4. Create Stream
        stream, created = Stream.objects.get_or_create(
            code='SCIENCE',
            defaults={
                'name': 'Science',
                'description': 'Science Stream',
                'available_from_class': cls
            }
        )
        print(f"Stream: {stream} (Created: {created})")

        # 5. Create Test Admin User
        user_email = 'testadmin@school.com'
        if not User.objects.filter(email=user_email).exists():
            User.objects.create_superuser(
                email=user_email,
                password='TestPass123!',
                first_name='Test',
                last_name='Admin',
                tenant=tenant
            )
            print(f"Superuser created: {user_email}")
        else:
            print(f"Superuser already exists: {user_email}")

if __name__ == '__main__':
    setup()
