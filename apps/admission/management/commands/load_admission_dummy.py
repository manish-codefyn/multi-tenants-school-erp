import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker
from apps.admission.models import (
    AdmissionCycle, AdmissionProgram, OnlineApplication, 
    ApplicationGuardian, ApplicationDocument
)
from apps.academics.models import AcademicYear
from django_tenants.utils import schema_context
from apps.core.utils.tenant import tenant_context
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Loads dummy data for the admission app'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Tenant schema name')
        parser.add_argument('--count', type=int, default=10, help='Number of applications to create')

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        count = options['count']
        fake = Faker('en_IN')

        if tenant_schema:
            try:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
                with schema_context(tenant.schema_name):
                    with tenant_context(tenant):
                        self.create_dummy_data(fake, count, tenant)
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant {tenant_schema} not found'))
        else:
            # If no tenant specified, try to run for all active tenants or just warn
            self.stdout.write(self.style.WARNING('No tenant specified. Running in current context (be careful if public).'))
            self.create_dummy_data(fake, count)

    def create_dummy_data(self, fake, count, tenant=None):
        self.stdout.write('Creating admission dummy data...')
        
        # 1. Ensure Academic Year
        academic_year, created = AcademicYear.objects.get_or_create(
            name="2024-2025",
            defaults={
                'start_date': timezone.now().date().replace(month=4, day=1),
                'end_date': timezone.now().date().replace(year=timezone.now().year + 1, month=3, day=31),
                'code': 'AY-2024-25',
                'is_active': True
            }
        )

        # 2. Create Admission Cycle
        cycle, created = AdmissionCycle.objects.get_or_create(
            code="ADM-2024-25",
            defaults={
                'name': "Admission 2024-2025",
                'academic_year': academic_year,
                'start_date': timezone.now() - timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=60),
                'status': 'ACTIVE',
                'application_fee': 500.00,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Admission Cycle: {cycle}'))

        # 3. Create Programs
        programs = []
        classes = ['Nursery', 'LKG', 'UKG', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5']
        for cls in classes:
            program, created = AdmissionProgram.objects.get_or_create(
                admission_cycle=cycle,
                class_grade=cls,
                defaults={
                    'program_name': f"{cls} Admission",
                    'program_type': 'PRIMARY' if 'Class' in cls else 'NURSERY',
                    'total_seats': 40,
                    'general_seats': 30,
                    'min_age_years': 3 if 'Nursery' in cls else 5,
                    'application_fee': 500.00,
                    'tuition_fee': 25000.00,
                    'is_active': True
                }
            )
            programs.append(program)
        
        self.stdout.write(self.style.SUCCESS(f'Ensured {len(programs)} programs exist'))

        # 4. Create Applications
        for _ in range(count):
            program = random.choice(programs)
            
            # Personal Info
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Calculate valid DOB based on program
            min_age = program.min_age_years
            max_age = min_age + 2  # Assuming 2 years window
            dob = fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)
            
            app = OnlineApplication.objects.create(
                tenant=tenant,
                admission_cycle=cycle,
                program=program,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                gender=random.choice(['M', 'F']),
                category=random.choice(['GENERAL', 'OBC', 'SC', 'ST']),
                email=fake.email(),
                phone=f"+91{fake.msisdn()[3:]}",
                address_line1=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                pincode=fake.postcode(),
                country="India",
                previous_school=f"{fake.city()} Public School",
                previous_qualification=f"Class {random.randint(1, 10)}",
                status=random.choice(['DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADMITTED']),
                submission_date=timezone.now() if random.choice([True, False]) else None
            )
            
            # Guardians
            ApplicationGuardian.objects.create(
                application=app,
                relation='FATHER',
                full_name=f"{fake.first_name_male()} {last_name}",
                email=fake.email(),
                phone=f"+91{fake.msisdn()[3:]}",
                occupation='SERVICE',
                is_primary=True,
                address_line1=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                pincode=fake.postcode()
            )
            
            ApplicationGuardian.objects.create(
                application=app,
                relation='MOTHER',
                full_name=f"{fake.first_name_female()} {last_name}",
                email=fake.email(),
                phone=f"+91{fake.msisdn()[3:]}",
                occupation='HOUSEWIFE',
                is_primary=False,
                address_line1=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                pincode=fake.postcode()
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} dummy applications'))
