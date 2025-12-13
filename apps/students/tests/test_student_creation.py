from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.students.models import Student, StudentIdentification, StudentMedicalInfo
from apps.tenants.models import Tenant, Domain
from apps.academics.models import AcademicYear, SchoolClass, Section
from apps.students.views import StudentCreateView
from apps.students.forms import StudentForm
from datetime import date
import uuid

User = get_user_model()

class StudentCreationTest(TestCase):
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant(
            name="Test School",
            schema_name="test_school",
            subdomain="test-school", # Assuming logic uses this or similar
            status="active"
        )
        self.tenant.auto_create_schema = False
        self.tenant.save()
        
        # Create a domain for the tenant (important for email generation)
        self.domain = Domain.objects.create(
            tenant=self.tenant,
            domain="test-school.com",
            is_primary=True
        )
        
        # Create related academic objects
        self.academic_year = AcademicYear.objects.create(
            name="2024-2025",
            code="AY2425",
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            tenant=self.tenant
        )
        
        self.school_class = SchoolClass.objects.create(
            name="Class 1",
            numeric_name=1,
            code="C1",
            level="PRIMARY",
            order=1,
            tenant=self.tenant
        )
        
        self.section = Section.objects.create(
            name="A",
            code="A",
            class_name=self.school_class,
            tenant=self.tenant
        )

    def test_student_creation_with_user_account(self):
        """
        Test creating a student and generating a user account.
        This mimics the flow in StudentCreateView.
        """
        # Prepare form data
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '2015-01-01',
            'gender': 'MALE',
            'admission_date': date.today(),
            'academic_year': self.academic_year.id,
            'current_class': self.school_class.id,
            'section': self.section.id,
            'create_user_account': True,
            # Add other required fields if any
        }
        
        # Initialize form with tenant
        form = StudentForm(data=form_data, tenant=self.tenant)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        # Save student (mimic view logic)
        student = form.save(commit=False)
        student.tenant = self.tenant
        student.save()
        
        # Check if student is created
        self.assertIsNotNone(student.id)
        
        # Create user account (this triggers generate_institutional_email and potential errors)
        # Verify no RelatedObjectDoesNotExist is raised
        try:
            student.create_user_account()
        except Exception as e:
            self.fail(f"create_user_account raised exception: {e}")
            
        # Verify user is linked
        student.refresh_from_db()
        self.assertIsNotNone(student.user)
        self.assertEqual(student.user.email, student.institutional_email)
        self.assertTrue(student.institutional_email.endswith('@test-school.com'))
