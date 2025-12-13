from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from apps.admission.forms import AdmissionApplicationForm
from apps.admission.models import AdmissionCycle, AdmissionProgram
from apps.academics.models import AcademicYear
from apps.tenants.models import Tenant

class AdmissionFormTests(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(name="Test School", schema_name="test_school", domain_url="test.school.com")
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            code="AY2425"
        )
        
        # Create admission cycle
        self.cycle = AdmissionCycle.objects.create(
            name="Admission 2024",
            academic_year=self.academic_year,
            code="ADM2024",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status="ACTIVE",
            tenant=self.tenant
        )
        
        # Create program
        self.program = AdmissionProgram.objects.create(
            admission_cycle=self.cycle,
            program_name="Class 1",
            program_type="PRIMARY",
            class_grade="1",
            total_seats=60,
            general_seats=40,
            application_fee=500,
            tuition_fee=50000,
            min_age_years=5,
            tenant=self.tenant
        )

    def test_form_validation_basic(self):
        """Test basic form validation"""
        form_data = {
            'admission_cycle': self.cycle.id,
            'program': self.program.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': date(2018, 1, 1),
            'gender': 'M',
            'category': 'GENERAL',
            'email': 'john@example.com',
            'confirm_email': 'john@example.com',
            'accept_terms': True,
            'phone': '9876543210'
        }
        form = AdmissionApplicationForm(data=form_data, tenant=self.tenant)
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_confirmation_mismatch(self):
        """Test email mismatch error"""
        form_data = {
            'admission_cycle': self.cycle.id,
            'program': self.program.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': date(2018, 1, 1),
            'email': 'john@example.com',
            'confirm_email': 'wrong@example.com',
            'accept_terms': True
        }
        form = AdmissionApplicationForm(data=form_data, tenant=self.tenant)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_email', form.errors)

    def test_age_eligibility_validation(self):
        """Test age validation in form"""
        # Too young
        too_young_dob = date.today() - timedelta(days=int(2 * 365))
        form_data = {
            'admission_cycle': self.cycle.id,
            'program': self.program.id,
            'first_name': 'Baby',
            'last_name': 'Doe',
            'date_of_birth': too_young_dob,
            'accept_terms': True
        }
        form = AdmissionApplicationForm(data=form_data, tenant=self.tenant)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)
