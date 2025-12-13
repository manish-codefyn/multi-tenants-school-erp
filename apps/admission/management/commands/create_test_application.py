from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.admission.models import AdmissionCycle, AdmissionProgram, OnlineApplication
from apps.admission.forms import AdmissionApplicationForm
from apps.academics.models import AcademicYear
from apps.users.models import User

class Command(BaseCommand):
    help = 'Test admission application form'

    def handle(self, *args, **kwargs):
        # Get the first non-public tenant
        tenant = Tenant.objects.exclude(schema_name='public').first()
        if not tenant:
            self.stdout.write(self.style.ERROR("No tenant found. Please create a tenant first."))
            return

        self.stdout.write(f"Using tenant: {tenant.schema_name}")
        
        from apps.core.utils.tenant import tenant_context
        from django.db import connection
        connection.set_tenant(tenant)

        with schema_context(tenant.schema_name), tenant_context(tenant):
            # 1. Ensure Academic Year exists
            academic_year = AcademicYear.objects.filter(is_active=True).first()
            if not academic_year:
                self.stdout.write("Creating Academic Year...")
                academic_year = AcademicYear.objects.create(
                    name=f"AY {timezone.now().year}-{timezone.now().year + 1}",
                    code=f"AY-{timezone.now().year}",
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=365),
                    is_active=True
                )
            self.stdout.write(f"Academic Year: {academic_year}")

            # 2. Ensure Admission Cycle exists
            cycle = AdmissionCycle.objects.filter(is_active=True, status='ACTIVE').first()
            if not cycle:
                self.stdout.write("Creating Admission Cycle...")
                cycle = AdmissionCycle.objects.create(
                    name="Test Admission Cycle",
                    code="ADM-TEST-2024",
                    academic_year=academic_year,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=90),
                    status='ACTIVE',
                    is_active=True
                )
            self.stdout.write(f"Admission Cycle: {cycle}")

            # 3. Ensure Admission Program exists
            program = AdmissionProgram.objects.filter(admission_cycle=cycle, is_active=True).first()
            if not program:
                self.stdout.write("Creating Admission Program...")
                program = AdmissionProgram.objects.create(
                    admission_cycle=cycle,
                    program_name="Grade 1",
                    program_type="PRIMARY",
                    class_grade="1",
                    total_seats=50,
                    general_seats=50,
                    application_fee=500.00,
                    tuition_fee=50000.00,
                    is_active=True
                )
            self.stdout.write(f"Admission Program: {program}")

            # Clean up existing application/user
            OnlineApplication.objects.filter(email='teststudent@example.com', admission_cycle=cycle).delete()
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.filter(email='teststudent@example.com').delete()

            # 4. Prepare Form Data
            form_data = {
                'admission_cycle': cycle.id,
                'program': program.id,
                'first_name': 'Test',
                'last_name': 'Student',
                'date_of_birth': '2015-01-01',
                'gender': 'M', 
                'category': 'GENERAL',
                'blood_group': 'O+',
                'nationality': 'Indian',
                'religion': 'Hindu',
                'email': 'teststudent@example.com',
                'confirm_email': 'teststudent@example.com',
                'phone': '+919876543210',
                'address_line1': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'pincode': '123456',
                'country': 'India',
                'previous_school': 'Test School',
                'previous_qualification': 'Kindergarten',
                'accept_terms': True,
                'create_account': True,
                'password': 'TestPassword123!',
                'confirm_password': 'TestPassword123!',
            }

            # 5. Instantiate and Validate Form
            # Create an instance with tenant set
            instance = OnlineApplication(tenant=tenant)
            form = AdmissionApplicationForm(data=form_data, tenant=tenant, instance=instance)
            
            if form.is_valid():
                self.stdout.write("Form is valid.")
                # Save the form
                application = form.save()
                self.stdout.write(self.style.SUCCESS(f"Application created: {application.application_number}"))
                
                # Verify User creation
                if form.cleaned_data.get('create_account'):
                    user = User.objects.filter(email='teststudent@example.com').first()
                    if user:
                        self.stdout.write(self.style.SUCCESS(f"User created: {user.email}"))
                    else:
                        self.stdout.write(self.style.ERROR("FAIL: User was not created."))
                
            else:
                self.stdout.write(self.style.ERROR("Form is invalid."))
                self.stdout.write(str(form.errors))
