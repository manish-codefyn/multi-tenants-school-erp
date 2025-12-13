from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from apps.admission.models import AdmissionCycle, AdmissionProgram, OnlineApplication
from apps.academics.models import AcademicYear
import datetime

class AdmissionModelTests(TestCase):
    def setUp(self):
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            code="AY2425"
        )
        
        # Create active admission cycle
        self.cycle = AdmissionCycle.objects.create(
            name="Admission 2024",
            academic_year=self.academic_year,
            code="ADM2024",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            status="ACTIVE"
        )
        
        # Create program
        self.program = AdmissionProgram.objects.create(
            admission_cycle=self.cycle,
            program_name="Class 1 General",
            program_type="PRIMARY",
            class_grade="1",
            total_seats=60,
            general_seats=40,
            application_fee=500,
            tuition_fee=50000,
            min_age_years=5
        )

    def test_admission_cycle_is_open(self):
        """Test cycle open status logic"""
        self.assertTrue(self.cycle.is_open)
        
        # Test closed status
        self.cycle.status = "CLOSED"
        self.cycle.save()
        self.assertFalse(self.cycle.is_open)
        
        # Test expired dates
        self.cycle.status = "ACTIVE"
        self.cycle.end_date = timezone.now() - timedelta(days=1)
        self.cycle.save()
        self.assertFalse(self.cycle.is_open)

    def test_program_age_eligibility(self):
        """Test age eligibility logic"""
        # 5.5 years old (should be eligible)
        dob_eligible = date.today() - timedelta(days=int(5.5 * 365))
        self.assertTrue(self.program.check_age_eligibility(dob_eligible))
        
        # 4 years old (should be ineligible)
        dob_ineligible = date.today() - timedelta(days=int(4 * 365))
        self.assertFalse(self.program.check_age_eligibility(dob_ineligible))

    def test_application_number_generation(self):
        """Test application number generation"""
        app = OnlineApplication.objects.create(
            admission_cycle=self.cycle,
            program=self.program,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2018, 1, 1),
            email="john@example.com",
            status="SUBMITTED"
        )
        app.refresh_from_db()
        self.assertTrue(app.application_number.startswith(f"APP-{self.cycle.code}-"))
        
        # Create second application
        app2 = OnlineApplication.objects.create(
            admission_cycle=self.cycle,
            program=self.program,
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(2018, 1, 1),
            email="jane@example.com",
            status="SUBMITTED"
        )
        app2.refresh_from_db()
        # Should increment
        num1 = int(app.application_number.split('-')[-1])
        num2 = int(app2.application_number.split('-')[-1])
        self.assertEqual(num2, num1 + 1)
