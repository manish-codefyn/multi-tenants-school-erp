import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import schema_context
from apps.core.utils.tenant import tenant_context
from faker import Faker

from apps.tenants.models import Tenant
from apps.students.models import Student, Guardian, StudentAddress
from apps.academics.models import AcademicYear, SchoolClass, Section, Stream

class Command(BaseCommand):
    help = 'Generates dummy students data for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Schema name of the tenant')
        parser.add_argument('--count', type=int, default=50, help='Number of students to create')

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        count = options['count']
        fake = Faker('en_IN')

        if not tenant_schema:
            self.stdout.write(self.style.ERROR('Please provide a tenant schema name using --tenant'))
            return

        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Tenant with schema {tenant_schema} not found'))
            return

        self.stdout.write(f'Creating students dummy data for tenant: {tenant.name} ({tenant_schema})...')

        with schema_context(tenant_schema):
            with tenant_context(tenant):
                self.create_dummy_data(fake, count, tenant)

    def create_dummy_data(self, fake, count, tenant):
        # Ensure Academic Year
        academic_year, _ = AcademicYear.objects.get_or_create(
            code=f"AY-{timezone.now().year}-{timezone.now().year+1}",
            defaults={
                "name": f"Academic Year {timezone.now().year}-{timezone.now().year+1}",
                "start_date": timezone.now().date().replace(month=4, day=1),
                "end_date": timezone.now().date().replace(year=timezone.now().year+1, month=3, day=31),
                "is_current": True
            }
        )

        # Ensure Classes and Sections
        classes = []
        for i in range(1, 13):
            cls, _ = SchoolClass.objects.get_or_create(
                code=f"CLS-{i:02d}",
                defaults={
                    "name": f"Class {i}",
                    "numeric_name": i,
                    "level": "PRIMARY" if i <= 5 else ("MIDDLE" if i <= 8 else ("HIGH" if i <= 10 else "SENIOR")),
                    "order": i
                }
            )
            
            # Create sections
            for sec_code in ['A', 'B']:
                Section.objects.get_or_create(
                    class_name=cls,
                    name=sec_code,
                    defaults={
                        "code": f"{cls.code}-{sec_code}",
                        "max_strength": 40
                    }
                )
            classes.append(cls)

        self.stdout.write(self.style.SUCCESS(f'Ensured academic year and classes exist'))

        # Create Students
        created_count = 0
        for i in range(count):
            try:
                # Select random class and section
                school_class = random.choice(classes)
                section = random.choice(school_class.sections.all())
                
                # Personal Info
                gender = random.choice(['M', 'F'])
                first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
                last_name = fake.last_name()
                
                # Calculate valid DOB based on class
                # Approx age = class + 5
                target_age = school_class.numeric_name + 5
                dob = fake.date_of_birth(minimum_age=target_age-1, maximum_age=target_age+1)
                
                # Clean email - ensure lowercase and remove any spaces
                email_first_name = first_name.lower().replace(" ", "")
                email_last_name = last_name.lower().replace(" ", "")
                personal_email = f"{email_first_name}.{email_last_name}{random.randint(1000,9999)}@example.com"
                
                student = Student.objects.create(
                    tenant=tenant,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob,
                    gender=gender,
                    blood_group=random.choice([c[0] for c in Student.BLOOD_GROUP_CHOICES]),
                    nationality="Indian",
                    religion=random.choice([c[0] for c in Student.RELIGION_CHOICES]),
                    category=random.choice([c[0] for c in Student.CATEGORY_CHOICES]),
                    
                    # Contact - FIXED: Use lowercase for email
                    personal_email=personal_email,
                    mobile_primary=f"+91{fake.msisdn()[3:]}",
                    reg_no=f"UNIV-{timezone.now().year}-{random.randint(10000, 99999)}",
                    
                    # Academic
                    academic_year=academic_year,
                    current_class=school_class,
                    section=section,
                    admission_type="REGULAR",
                    enrollment_date=academic_year.start_date,
                    status="ACTIVE"
                )
                
                # Guardians
                Guardian.objects.create(
                    student=student,
                    relation='FATHER',
                    full_name=f"{fake.first_name_male()} {last_name}",
                    email=fake.email(),
                    phone_primary=f"+91{fake.msisdn()[3:]}",
                    occupation='SERVICE',
                    is_primary=True
                )
                
                Guardian.objects.create(
                    student=student,
                    relation='MOTHER',
                    full_name=f"{fake.first_name_female()} {last_name}",
                    email=fake.email(),
                    phone_primary=f"+91{fake.msisdn()[3:]}",
                    occupation='HOUSEWIFE',
                    is_primary=False
                )
                
                # Address
                StudentAddress.objects.create(
                    student=student,
                    address_type='PERMANENT',
                    address_line1=fake.street_address(),
                    city=fake.city(),
                    state=fake.state(),
                    pincode=fake.postcode(),
                    country="India"
                )
                
                created_count += 1
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'Created {i + 1} students...')
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to create student: {str(e)}'))
                # Show more specific error details
                if hasattr(e, 'message_dict'):
                    self.stdout.write(self.style.WARNING(f'Error details: {e.message_dict}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} dummy students'))